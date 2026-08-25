import json
import logging
import time
from urllib.error import URLError
from urllib.request import urlopen

from fastapi import HTTPException, status
from jose import jwk, jwt
from jose.exceptions import JOSEError

logger = logging.getLogger(__name__)

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
APPLE_AUDIENCE = "com.lanceon.app"

_apple_keys: list[dict] = []
_apple_keys_expires_at = 0.0


def _load_apple_keys(force: bool = False) -> list[dict]:
    global _apple_keys, _apple_keys_expires_at
    now = time.time()
    if not force and _apple_keys and now < _apple_keys_expires_at:
        return _apple_keys

    with urlopen(APPLE_KEYS_URL, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    keys = payload.get("keys") or []
    _apple_keys = keys
    _apple_keys_expires_at = now + 3600
    return keys


def verify_apple_identity_token(identity_token: str) -> dict:
    try:
        header = jwt.get_unverified_header(identity_token)
        kid = header.get("kid")
        matching = next((item for item in _load_apple_keys() if item.get("kid") == kid), None)
        if not matching:
            matching = next(
                (item for item in _load_apple_keys(force=True) if item.get("kid") == kid),
                None,
            )
        if not matching:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token Apple invalido",
            )

        rsa_key = jwk.construct(matching)
        public_pem = rsa_key.to_pem()
        if isinstance(public_pem, bytes):
            public_pem = public_pem.decode("utf-8")

        claims = jwt.decode(
            identity_token,
            public_pem,
            algorithms=["RS256"],
            audience=APPLE_AUDIENCE,
            issuer=APPLE_ISSUER,
        )
    except HTTPException:
        raise
    except (JOSEError, URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError) as exc:
        logger.warning("Apple token verification failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Apple invalido",
        ) from exc

    if not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token Apple invalido",
        )
    return claims
