import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from cryptography.hazmat.primitives import serialization
from cryptography.x509 import load_pem_x509_certificate
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.config import settings

FIREBASE_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
)

_firebase_certs: dict[str, str] | None = None
_firebase_certs_expires_at = 0.0


def _load_firebase_certs() -> dict[str, str]:
    global _firebase_certs, _firebase_certs_expires_at

    now = time.time()
    if _firebase_certs and now < _firebase_certs_expires_at:
        return _firebase_certs

    try:
        with urlopen(FIREBASE_CERTS_URL, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
            cache_control = response.headers.get("Cache-Control", "")
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nao foi possivel validar o token Firebase",
        ) from exc

    max_age = 3600
    for part in cache_control.split(","):
        part = part.strip()
        if part.startswith("max-age="):
            try:
                max_age = int(part.split("=", 1)[1])
            except ValueError:
                pass

    _firebase_certs = payload
    _firebase_certs_expires_at = now + max(60, max_age)
    return payload


def _public_key_from_x509(cert_pem: str) -> str:
    certificate = load_pem_x509_certificate(cert_pem.encode("utf-8"))
    return (
        certificate.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )


def verify_firebase_id_token(id_token: str) -> dict:
    project_id = settings.firebase_project_id
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Auth nao configurado no servidor",
        )

    try:
        header = jwt.get_unverified_header(id_token)
        kid = header.get("kid")
        certs = _load_firebase_certs()
        if not kid or kid not in certs:
            raise JWTError("Certificado Firebase desconhecido")

        payload = jwt.decode(
            id_token,
            _public_key_from_x509(certs[kid]),
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}",
        )
    except (JWTError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Firebase invalido",
        ) from exc

    if payload.get("email_verified") in ("false", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail Firebase nao verificado",
        )

    if not payload.get("email") or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Firebase incompleto",
        )

    return payload


def identity_from_auth_payload(payload: dict) -> dict:
    firebase = payload.get("firebase") or {}
    identities = firebase.get("identities") or {}
    google_ids = identities.get("google.com") or []
    google_id = str(google_ids[0]) if google_ids else str(payload.get("sub") or "")

    return {
        "email": payload.get("email"),
        "google_id": google_id,
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }
