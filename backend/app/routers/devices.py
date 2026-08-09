from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_court_by_device_key
from app.models import CaptureTrigger, CaptureTriggerStatus, Device
from app.schemas import DeviceHeartbeat, MessageResponse, PendingTriggerItem

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/heartbeat", response_model=MessageResponse)
def device_heartbeat(
    payload: DeviceHeartbeat,
    db: Session = Depends(get_db),
    x_device_key: str = Header(..., alias="X-Device-Key"),
):
    court = get_court_by_device_key(x_device_key, db)
    device = (
        db.query(Device)
        .filter(Device.court_id == court.id, Device.camera_index == payload.camera_index)
        .first()
    )
    if not device:
        raise HTTPException(status_code=404, detail="Camera nao encontrada")

    device.is_online = True
    device.last_heartbeat = datetime.now(timezone.utc)
    db.commit()
    return MessageResponse(message="Heartbeat recebido")


@router.get("/pending-triggers", response_model=list[PendingTriggerItem])
def claim_pending_triggers(
    db: Session = Depends(get_db),
    x_device_key: str = Header(..., alias="X-Device-Key"),
):
    """Capture agent polls this endpoint to receive mobile PRONTO triggers."""
    court = get_court_by_device_key(x_device_key, db)
    now = datetime.now(timezone.utc)

    # Drop very old unclaimed requests
    db.query(CaptureTrigger).filter(
        CaptureTrigger.court_id == court.id,
        CaptureTrigger.status == CaptureTriggerStatus.pending,
        CaptureTrigger.created_at < now - timedelta(minutes=10),
    ).update(
        {"status": CaptureTriggerStatus.expired},
        synchronize_session=False,
    )

    pending = (
        db.query(CaptureTrigger)
        .filter(
            CaptureTrigger.court_id == court.id,
            CaptureTrigger.status == CaptureTriggerStatus.pending,
        )
        .order_by(CaptureTrigger.created_at.asc())
        .limit(20)
        .all()
    )

    items: list[PendingTriggerItem] = []
    for trigger in pending:
        trigger.status = CaptureTriggerStatus.claimed
        trigger.claimed_at = now
        items.append(
            PendingTriggerItem(
                id=trigger.id,
                camera_index=trigger.camera_index,
                created_at=trigger.created_at,
            )
        )

    db.commit()
    return items
