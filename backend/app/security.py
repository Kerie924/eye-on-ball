import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models import User, UserRole

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user_id: int, role: UserRole) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "role": role.value, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def generate_device_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def ensure_admin_user(db: Session) -> None:
    existing = db.query(User).filter(User.email == settings.admin_email).first()
    if existing:
        return

    admin = User(
        email=settings.admin_email,
        password_hash=hash_password(settings.admin_password),
        full_name=settings.admin_name,
        role=UserRole.admin,
        is_active=True,
        is_approved=True,
    )
    db.add(admin)
    db.commit()
