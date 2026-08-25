import logging
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from jose import jwt

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.emailer import email_configured, public_smtp_error, send_password_reset_email
from app.firebase_auth import identity_from_auth_payload, verify_firebase_id_token
from app.apple_auth import verify_apple_identity_token
from app.google_app_page import google_app_html
from app.reset_password_page import reset_password_html
from app.models import User, UserRole
from app.schemas import (
    AppleAuthRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleAuthRequest,
    MessageResponse,
    ResetPasswordRequest,
    TokenResponse,
    UserLogin,
    UserProfileUpdate,
    UserRegister,
    UserResponse,
)
from app.security import create_access_token, hash_password, hash_reset_token, verify_password

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google-app", response_class=HTMLResponse, include_in_schema=False)
def google_app_sign_in(continue_url: str = Query(alias="continue")):
    return google_app_html(continue_url)


@router.get("/reset-password-app", response_class=HTMLResponse, include_in_schema=False)
def reset_password_app(token: str = Query(min_length=10)):
    return reset_password_html(token)


def _token_issuer(id_token: str) -> str:
    try:
        return str(jwt.get_unverified_claims(id_token).get("iss") or "")
    except Exception:
        return ""


def verify_id_token(id_token: str) -> dict:
    issuer = _token_issuer(id_token)
    if issuer.startswith("https://securetoken.google.com/"):
        return verify_firebase_id_token(id_token)
    return verify_google_id_token(id_token)


def verify_google_id_token(id_token: str) -> dict:
    import json

    query = urlencode({"id_token": id_token})
    url = f"https://oauth2.googleapis.com/tokeninfo?{query}"
    try:
        with urlopen(url, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google invalido",
        ) from exc

    allowed_audiences = settings.google_client_ids
    if allowed_audiences and payload.get("aud") not in allowed_audiences:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google nao corresponde ao Client ID configurado",
        )

    if payload.get("email_verified") in ("false", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail Google nao verificado",
        )

    email = payload.get("email")
    google_id = payload.get("sub")
    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Google incompleto",
        )

    return payload


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail ja esta cadastrado",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_approved=payload.role == UserRole.athlete,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token)


@router.post("/google", response_model=TokenResponse)
def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    identity = identity_from_auth_payload(verify_id_token(payload.id_token))
    email = identity["email"]
    google_id = identity["google_id"]
    full_name = identity.get("name") or email.split("@")[0]
    avatar_url = identity.get("picture")

    if not email or not google_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao incompleto",
        )

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        user = db.query(User).filter(User.email == email).first()

    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta desativada",
            )
        user.google_id = google_id
        if avatar_url and not user.avatar_url:
            user.avatar_url = avatar_url
        if full_name:
            user.full_name = full_name
    else:
        user = User(
            email=email,
            password_hash=hash_password(token_urlsafe(24)),
            full_name=full_name,
            role=payload.role,
            is_approved=payload.role == UserRole.athlete,
            google_id=google_id,
            avatar_url=avatar_url,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@router.post("/apple", response_model=TokenResponse)
def apple_login(payload: AppleAuthRequest, db: Session = Depends(get_db)):
    claims = verify_apple_identity_token(payload.identity_token)
    apple_id = str(claims["sub"])
    email = (claims.get("email") or "").strip().lower()
    full_name = (payload.full_name or "").strip() or email.split("@")[0] or "Atleta"

    user = db.query(User).filter(User.apple_id == apple_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Conta desativada",
            )
        user.apple_id = apple_id
        if full_name and user.full_name in {"Atleta", email.split("@")[0]}:
            user.full_name = full_name
    else:
        if not email:
            email = f"apple-{apple_id[:12]}@privaterelay.appleid.com"
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail ja esta cadastrado",
            )
        user = User(
            email=email,
            password_hash=hash_password(token_urlsafe(24)),
            full_name=full_name or "Atleta",
            role=payload.role,
            is_approved=payload.role == UserRole.athlete,
            apple_id=apple_id,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    payload: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    if payload.email and payload.email != user.email:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este e-mail ja esta cadastrado",
            )
        user.email = payload.email

    if payload.full_name:
        user.full_name = payload.full_name

    if payload.avatar_url is not None:
        user.avatar_url = payload.avatar_url or None

    if payload.new_password:
        if not payload.current_password or not verify_password(
            payload.current_password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Senha atual incorreta",
            )
        user.password_hash = hash_password(payload.new_password)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/me", response_model=MessageResponse)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")

    user.is_active = False
    user.email = f"deleted-{user.id}-{token_urlsafe(6).lower()}@lanceonpara.com.br"
    user.full_name = "Conta excluida"
    user.password_hash = hash_password(token_urlsafe(24))
    user.google_id = None
    user.apple_id = None
    user.avatar_url = None
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return MessageResponse(message="Conta excluida")


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    if not email_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="E-mail de redefinicao nao configurado no servidor. Defina SMTP_HOST no .env da API.",
        )

    message = "Se o e-mail existir, voce recebera um link para redefinir a senha."
    user = db.query(User).filter(User.email == payload.email).first()

    if not user:
        return ForgotPasswordResponse(message=message)

    raw_token = token_urlsafe(32)
    user.reset_token = hash_reset_token(raw_token)
    user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    db.commit()

    public_api = settings.public_api_url.rstrip("/")
    reset_url = f"{public_api}/api/auth/reset-password-app?token={raw_token}"
    app_url = f"lanceon://reset-password?token={raw_token}"

    try:
        send_password_reset_email(user.email, reset_url, app_url)
    except Exception as exc:
        logger.exception("Falha ao enviar e-mail de redefinicao de senha")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Nao foi possivel enviar o e-mail: {public_smtp_error(exc)}",
        ) from None

    return ForgotPasswordResponse(message=message)


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(User.reset_token == hash_reset_token(payload.token))
        .first()
    )
    if not user or not user.reset_token_expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido ou expirado",
        )

    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalido ou expirado",
        )

    user.password_hash = hash_password(payload.password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    return MessageResponse(message="Senha atualizada com sucesso")
