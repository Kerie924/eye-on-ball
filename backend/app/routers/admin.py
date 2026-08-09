from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import require_admin
from app.models import (
    AccessRequestStatus,
    Court,
    CourtAccessRequest,
    Device,
    PlatformSettings,
    Recording,
    User,
    UserRole,
)
from app.platform_settings import ensure_platform_settings
from app.schemas import (
    ActivityItem,
    AdminCreateUser,
    AdminRecordingResponse,
    AdminUpdateUser,
    MessageResponse,
    PlatformSettingsResponse,
    PlatformSettingsUpdate,
    UserResponse,
)
from app.security import hash_password
from app.storage import generate_download_url

router = APIRouter(prefix="/admin", tags=["admin"])

AVG_CLIP_SIZE_MB = 5


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    payload: AdminCreateUser,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Este e-mail ja esta cadastrado")

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


@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: AdminUpdateUser,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    if user.id == admin.id and payload.is_active is False:
        raise HTTPException(status_code=400, detail="Voce nao pode desativar sua propria conta")

    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_approved is not None:
        user.is_approved = payload.is_approved

    db.commit()
    db.refresh(user)
    return user


@router.get("/settings", response_model=PlatformSettingsResponse)
def get_settings(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return ensure_platform_settings(db)


@router.put("/settings", response_model=PlatformSettingsResponse)
def update_settings(
    payload: PlatformSettingsUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    row = ensure_platform_settings(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    platform = ensure_platform_settings(db)

    recordings_total = db.query(Recording).count()
    recordings_today = (
        db.query(Recording).filter(Recording.created_at >= today_start).count()
    )
    active_users = (
        db.query(User)
        .filter(User.is_active.is_(True), User.role != UserRole.admin)
        .count()
    )
    storage_used_gb = round((recordings_total * AVG_CLIP_SIZE_MB) / 1024, 2)
    storage_limit_gb = platform.storage_limit_tb * 1024

    recordings_by_day = []
    for offset in range(6, -1, -1):
        day = (now - timedelta(days=offset)).date()
        day_start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc)
        day_end = day_start + timedelta(days=1)
        count = (
            db.query(Recording)
            .filter(Recording.created_at >= day_start, Recording.created_at < day_end)
            .count()
        )
        recordings_by_day.append({"date": day.isoformat(), "count": count})

    courts = db.query(Court).filter(Court.is_active.is_(True)).all()
    court_status = []
    for court in courts:
        devices = db.query(Device).filter(Device.court_id == court.id).all()
        online = any(device.is_online for device in devices)
        court_status.append(
            {
                "id": court.id,
                "name": court.name,
                "online": online,
                "device_count": len(devices),
            }
        )

    online_courts = sum(1 for court in court_status if court["online"])
    offline_courts = len(court_status) - online_courts
    devices_online = db.query(Device).filter(Device.is_online.is_(True)).count()
    devices_total = db.query(Device).count()

    return {
        "users": db.query(User).count(),
        "active_users": active_users,
        "courts": len(courts),
        "courts_online": online_courts,
        "courts_offline": offline_courts,
        "devices_online": devices_online,
        "devices_total": devices_total,
        "devices_offline": devices_total - devices_online,
        "recordings": recordings_total,
        "recordings_today": recordings_today,
        "pending_access_requests": db.query(CourtAccessRequest)
        .filter(CourtAccessRequest.status == AccessRequestStatus.pending)
        .count(),
        "pending_scouts": db.query(User)
        .filter(
            User.role == UserRole.scout,
            User.is_approved.is_(False),
            User.is_active.is_(True),
        )
        .count(),
        "storage_used_gb": storage_used_gb,
        "storage_limit_gb": storage_limit_gb,
        "storage_limit_tb": platform.storage_limit_tb,
        "recordings_by_day": recordings_by_day,
        "court_status": court_status,
    }


@router.get("/activity", response_model=list[ActivityItem])
def recent_activity(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    items: list[ActivityItem] = []

    recordings = (
        db.query(Recording)
        .options(joinedload(Recording.court))
        .order_by(Recording.created_at.desc())
        .limit(5)
        .all()
    )
    for recording in recordings:
        items.append(
            ActivityItem(
                message=f"Nova gravacao na quadra {recording.court.name}",
                created_at=recording.created_at,
                kind="recording",
            )
        )

    requests = (
        db.query(CourtAccessRequest)
        .options(joinedload(CourtAccessRequest.user), joinedload(CourtAccessRequest.court))
        .filter(CourtAccessRequest.status == AccessRequestStatus.pending)
        .order_by(CourtAccessRequest.created_at.desc())
        .limit(5)
        .all()
    )
    for request in requests:
        items.append(
            ActivityItem(
                message=(
                    f"{request.user.full_name} solicitou acesso a {request.court.name}"
                ),
                created_at=request.created_at,
                kind="access_request",
            )
        )

    users = (
        db.query(User)
        .filter(User.role != UserRole.admin)
        .order_by(User.created_at.desc())
        .limit(5)
        .all()
    )
    for user in users:
        items.append(
            ActivityItem(
                message=f"Novo usuario cadastrado: {user.full_name} ({user.role.value})",
                created_at=user.created_at,
                kind="user",
            )
        )

    items.sort(key=lambda item: item.created_at, reverse=True)
    return items[:10]


@router.get("/recordings", response_model=list[AdminRecordingResponse])
def admin_list_recordings(
    court_id: int | None = None,
    status: str | None = Query(default=None, pattern="^(available|expired|all)$"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    now = datetime.now(timezone.utc)
    query = db.query(Recording).options(joinedload(Recording.court))

    if court_id is not None:
        query = query.filter(Recording.court_id == court_id)
    if status == "available":
        query = query.filter(Recording.expires_at > now)
    elif status == "expired":
        query = query.filter(Recording.expires_at <= now)

    recordings = query.order_by(Recording.triggered_at.desc()).all()
    result = []
    for recording in recordings:
        is_available = recording.expires_at > now
        result.append(
            AdminRecordingResponse(
                id=recording.id,
                court_id=recording.court_id,
                camera_index=recording.camera_index,
                duration_seconds=recording.duration_seconds,
                triggered_at=recording.triggered_at,
                expires_at=recording.expires_at,
                created_at=recording.created_at,
                court_name=recording.court.name,
                download_url=generate_download_url(recording.file_key)
                if is_available
                else None,
                status="available" if is_available else "expired",
            )
        )
    return result


@router.get("/scouts/pending", response_model=list[UserResponse])
def list_pending_scouts(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    scouts = (
        db.query(User)
        .filter(
            User.role == UserRole.scout,
            User.is_approved.is_(False),
            User.is_active.is_(True),
        )
        .order_by(User.created_at.asc())
        .all()
    )
    return scouts


@router.post("/scouts/{user_id}/approve", response_model=MessageResponse)
def approve_scout(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    scout = db.get(User, user_id)
    if not scout or scout.role != UserRole.scout:
        raise HTTPException(status_code=404, detail="Olheiro nao encontrado")
    if scout.is_approved:
        raise HTTPException(status_code=400, detail="Olheiro ja foi aprovado")

    scout.is_approved = True
    db.commit()
    return MessageResponse(message="Olheiro aprovado com sucesso")


@router.post("/scouts/{user_id}/reject", response_model=MessageResponse)
def reject_scout(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    scout = db.get(User, user_id)
    if not scout or scout.role != UserRole.scout:
        raise HTTPException(status_code=404, detail="Olheiro nao encontrado")
    if scout.is_approved:
        raise HTTPException(status_code=400, detail="Olheiro ja foi aprovado")

    scout.is_active = False
    db.commit()
    return MessageResponse(message="Cadastro de olheiro rejeitado")
