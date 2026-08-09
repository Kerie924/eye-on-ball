from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.dependencies import (
    get_accessible_court_ids,
    get_court_by_device_key,
    get_current_user,
    get_current_user_from_bearer_or_query,
    require_admin,
    user_can_access_court,
)
from app.models import CaptureTrigger, CaptureTriggerStatus, Court, Device, Recording, User
from app.schemas import (
    CaptureTriggerRequest,
    CaptureTriggerResponse,
    MessageResponse,
    RecordingResponse,
)
from app.storage import delete_file, generate_download_url, get_s3_client, upload_file

router = APIRouter(prefix="/recordings", tags=["recordings"])

TRIGGER_COOLDOWN_SECONDS = 5
DEVICE_ONLINE_WINDOW_SECONDS = 120


@router.post("/trigger", response_model=CaptureTriggerResponse)
def trigger_capture(
    payload: CaptureTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Queue a capture on the court mini PC (consumed by the capture agent)."""
    if not user_can_access_court(current_user, payload.court_id, db):
        raise HTTPException(status_code=403, detail="Sem acesso a esta quadra")

    court = db.get(Court, payload.court_id)
    if not court or not court.is_active:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")

    now = datetime.now(timezone.utc)
    recent = (
        db.query(CaptureTrigger)
        .filter(
            CaptureTrigger.court_id == payload.court_id,
            CaptureTrigger.requested_by_id == current_user.id,
            CaptureTrigger.created_at
            > now - timedelta(seconds=TRIGGER_COOLDOWN_SECONDS),
        )
        .first()
    )
    if recent:
        raise HTTPException(
            status_code=429,
            detail="Aguarde alguns segundos antes de gravar novamente",
        )

    devices = (
        db.query(Device)
        .filter(Device.court_id == payload.court_id)
        .order_by(Device.camera_index)
        .all()
    )
    if not devices:
        raise HTTPException(status_code=404, detail="Nenhuma camera cadastrada nesta quadra")

    if payload.camera_index is not None:
        devices = [d for d in devices if d.camera_index == payload.camera_index]
        if not devices:
            raise HTTPException(status_code=404, detail="Camera nao encontrada")

    online = False
    for device in devices:
        if device.last_heartbeat:
            hb = device.last_heartbeat
            if hb.tzinfo is None:
                hb = hb.replace(tzinfo=timezone.utc)
            if hb >= now - timedelta(seconds=DEVICE_ONLINE_WINDOW_SECONDS):
                online = True
                break

    cameras: list[int] = []
    for device in devices:
        db.add(
            CaptureTrigger(
                court_id=payload.court_id,
                camera_index=device.camera_index,
                requested_by_id=current_user.id,
                status=CaptureTriggerStatus.pending,
            )
        )
        cameras.append(device.camera_index)

    db.commit()

    if online:
        message = "Comando enviado. O lance sera gravado em instantes."
    else:
        message = (
            "Comando enfileirado, mas o dispositivo da quadra parece offline. "
            "Verifique se o software de captura esta rodando."
        )

    return CaptureTriggerResponse(
        message=message,
        court_id=court.id,
        court_name=court.name,
        cameras=cameras,
        device_online=online,
    )


@router.post("/upload", response_model=RecordingResponse, status_code=201)
async def upload_recording(
    camera_index: int = Form(..., ge=1, le=2),
    triggered_at: datetime = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    x_device_key: str = Header(..., alias="X-Device-Key"),
):
    court = get_court_by_device_key(x_device_key, db)
    device = (
        db.query(Device)
        .filter(Device.court_id == court.id, Device.camera_index == camera_index)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Camera nao encontrada")

    if triggered_at.tzinfo is None:
        triggered_at = triggered_at.replace(tzinfo=timezone.utc)

    expires_at = triggered_at + timedelta(hours=settings.recording_retention_hours)
    file_key = f"courts/{court.id}/camera-{camera_index}/{uuid4().hex}.mp4"

    upload_file(file.file, file_key, content_type=file.content_type or "video/mp4")

    recording = Recording(
        court_id=court.id,
        device_id=device.id,
        camera_index=camera_index,
        file_key=file_key,
        duration_seconds=settings.clip_duration_seconds,
        triggered_at=triggered_at,
        expires_at=expires_at,
    )
    db.add(recording)
    db.commit()
    db.refresh(recording)

    return RecordingResponse(
        id=recording.id,
        court_id=recording.court_id,
        camera_index=recording.camera_index,
        duration_seconds=recording.duration_seconds,
        triggered_at=recording.triggered_at,
        expires_at=recording.expires_at,
        created_at=recording.created_at,
        court_name=court.name,
    )


@router.get("", response_model=list[RecordingResponse])
def list_recordings(
    court_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    accessible_court_ids = get_accessible_court_ids(current_user, db)

    if not accessible_court_ids:
        return []

    query = (
        db.query(Recording)
        .options(joinedload(Recording.court))
        .filter(
            Recording.court_id.in_(accessible_court_ids),
            Recording.expires_at > now,
        )
        .order_by(Recording.triggered_at.desc())
    )

    if court_id is not None:
        if court_id not in accessible_court_ids:
            raise HTTPException(status_code=403, detail="Sem acesso a esta quadra")
        query = query.filter(Recording.court_id == court_id)

    recordings = query.all()
    return [
        RecordingResponse(
            id=recording.id,
            court_id=recording.court_id,
            camera_index=recording.camera_index,
            duration_seconds=recording.duration_seconds,
            triggered_at=recording.triggered_at,
            expires_at=recording.expires_at,
            created_at=recording.created_at,
            court_name=recording.court.name,
            download_url=generate_download_url(recording.file_key),
        )
        for recording in recordings
    ]


@router.get("/{recording_id}", response_model=RecordingResponse)
def get_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    recording = (
        db.query(Recording)
        .options(joinedload(Recording.court))
        .filter(Recording.id == recording_id, Recording.expires_at > now)
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Gravacao nao encontrada")

    if not user_can_access_court(current_user, recording.court_id, db):
        raise HTTPException(status_code=403, detail="Sem acesso a esta gravacao")

    return RecordingResponse(
        id=recording.id,
        court_id=recording.court_id,
        camera_index=recording.camera_index,
        duration_seconds=recording.duration_seconds,
        triggered_at=recording.triggered_at,
        expires_at=recording.expires_at,
        created_at=recording.created_at,
        court_name=recording.court.name,
        download_url=generate_download_url(recording.file_key),
    )


@router.get("/{recording_id}/stream")
def stream_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_bearer_or_query),
):
    """Auth-protected stream proxy so phones can play/download without direct MinIO access."""
    now = datetime.now(timezone.utc)
    recording = (
        db.query(Recording)
        .filter(Recording.id == recording_id, Recording.expires_at > now)
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Gravacao nao encontrada")

    if not user_can_access_court(current_user, recording.court_id, db):
        raise HTTPException(status_code=403, detail="Sem acesso a esta gravacao")

    client = get_s3_client()
    try:
        obj = client.get_object(Bucket=settings.s3_bucket, Key=recording.file_key)
    except Exception as exc:
        raise HTTPException(status_code=404, detail="Arquivo nao encontrado") from exc

    body = obj["Body"]
    content_type = obj.get("ContentType") or "video/mp4"

    def iterfile():
        while True:
            chunk = body.read(1024 * 256)
            if not chunk:
                break
            yield chunk

    headers = {
        "Content-Disposition": f'inline; filename="lance-{recording.id}.mp4"',
        "Accept-Ranges": "bytes",
        "Cache-Control": "private, max-age=60",
    }
    return StreamingResponse(iterfile(), media_type=content_type, headers=headers)


@router.get("/{recording_id}/download-link")
def recording_download_link(
    recording_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    recording = (
        db.query(Recording)
        .filter(Recording.id == recording_id, Recording.expires_at > now)
        .first()
    )
    if not recording:
        raise HTTPException(status_code=404, detail="Gravacao nao encontrada")

    if not user_can_access_court(current_user, recording.court_id, db):
        raise HTTPException(status_code=403, detail="Sem acesso a esta gravacao")

    return {"url": generate_download_url(recording.file_key)}


@router.delete("/{recording_id}", response_model=MessageResponse)
def delete_recording(
    recording_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    recording = db.get(Recording, recording_id)
    if not recording:
        raise HTTPException(status_code=404, detail="Gravacao nao encontrada")

    try:
        delete_file(recording.file_key)
    except Exception:
        pass

    db.delete(recording)
    db.commit()
    return MessageResponse(message="Gravacao excluida com sucesso")
