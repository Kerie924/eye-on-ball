from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AccessRequestStatus, Court, CourtAccess, CourtAccessRequest, Recording, User, UserRole
from app.security import decode_access_token

security_scheme = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)

# Extra minutes around the requested play window (clip timing / late trigger)
PLAY_WINDOW_PAD = timedelta(minutes=20)


def _user_from_token(token: str, db: Session) -> User:
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
        )

    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario nao encontrado ou inativo",
        )
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    return _user_from_token(credentials.credentials, db)


def get_current_user_from_bearer_or_query(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    token: str | None = Query(default=None),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """Allow Authorization header or ?token= for media players that cannot send headers."""
    raw = None
    if credentials and credentials.credentials:
        raw = credentials.credentials
    elif token:
        raw = token
    elif authorization and authorization.lower().startswith("bearer "):
        raw = authorization.split(" ", 1)[1].strip()

    if not raw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado",
        )
    return _user_from_token(raw, db)

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores",
        )
    return user


def require_athlete(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.athlete:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a atletas",
        )
    return user


def require_athlete_or_scout(user: User = Depends(get_current_user)) -> User:
    if user.role not in (UserRole.athlete, UserRole.scout):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a atletas e olheiros",
        )
    return user


def get_court_by_device_key(device_api_key: str, db: Session) -> Court:
    court = db.query(Court).filter(Court.device_api_key == device_api_key).first()
    if not court or not court.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Chave do dispositivo invalida",
        )
    return court


def user_can_access_court(user: User, court_id: int, db: Session) -> bool:
    if user.role == UserRole.admin:
        return True

    court = db.get(Court, court_id)
    if not court or not court.is_active:
        return False

    if user.role == UserRole.scout:
        return user.is_approved

    if user.role == UserRole.athlete:
        return (
            db.query(CourtAccess)
            .filter(CourtAccess.user_id == user.id, CourtAccess.court_id == court_id)
            .first()
            is not None
        )

    return False


def get_accessible_court_ids(user: User, db: Session) -> list[int]:
    """Any logged-in user can browse active courts. Access requests come later."""
    courts = db.query(Court.id).filter(Court.is_active.is_(True)).all()
    return [court.id for court in courts]


def user_can_view_recording(user: User, recording: Recording, db: Session) -> bool:
    """Logged-in users can watch clips from active courts (no approval gate yet)."""
    if user.role == UserRole.admin:
        return True
    court = getattr(recording, "court", None) or db.get(Court, recording.court_id)
    return bool(court and court.is_active)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def athlete_can_view_recording(user: User, recording: Recording, db: Session) -> bool:
    """Athletes only see clips inside an approved play-time window for that court."""
    if user.role != UserRole.athlete:
        return user_can_access_court(user, recording.court_id, db)

    if not user_can_access_court(user, recording.court_id, db):
        return False

    approved = (
        db.query(CourtAccessRequest)
        .filter(
            CourtAccessRequest.user_id == user.id,
            CourtAccessRequest.court_id == recording.court_id,
            CourtAccessRequest.status == AccessRequestStatus.approved,
        )
        .all()
    )
    timed = [row for row in approved if row.play_started_at and row.play_ended_at]
    if not timed:
        # Legacy approvals without a play window → full court (within retention)
        return True

    triggered = _as_utc(recording.triggered_at)
    for row in timed:
        start = _as_utc(row.play_started_at) - PLAY_WINDOW_PAD
        end = _as_utc(row.play_ended_at) + PLAY_WINDOW_PAD
        if start <= triggered <= end:
            return True
    return False
