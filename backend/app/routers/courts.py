from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import Court, Device, User, UserRole
from app.schemas import CourtCreate, CourtResponse, CourtUpdate, DeviceResponse, MessageResponse
from app.security import generate_device_api_key

router = APIRouter(prefix="/courts", tags=["courts"])


@router.post("", response_model=CourtResponse, status_code=status.HTTP_201_CREATED)
def create_court(
    payload: CourtCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    existing = db.query(Court).filter(Court.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ja existe uma quadra com este nome",
        )

    court = Court(
        name=payload.name,
        address=payload.address,
        device_api_key=generate_device_api_key(),
    )
    db.add(court)
    db.flush()

    for camera_index in (1, 2):
        db.add(
            Device(
                court_id=court.id,
                camera_index=camera_index,
                name=f"Camera {camera_index}",
            )
        )

    db.commit()
    db.refresh(court)
    return court


@router.get("", response_model=list[CourtResponse])
def list_courts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    courts = db.query(Court).filter(Court.is_active.is_(True)).order_by(Court.name).all()
    if current_user.role != UserRole.admin:
        return [
            CourtResponse(
                id=court.id,
                name=court.name,
                address=court.address,
                is_active=court.is_active,
                created_at=court.created_at,
            )
            for court in courts
        ]
    return courts


@router.patch("/{court_id}", response_model=CourtResponse)
def update_court(
    court_id: int,
    payload: CourtUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")

    if payload.name and payload.name != court.name:
        existing = db.query(Court).filter(Court.name == payload.name).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Ja existe uma quadra com este nome",
            )
        court.name = payload.name

    if payload.address is not None:
        court.address = payload.address

    db.commit()
    db.refresh(court)
    return court


@router.get("/{court_id}", response_model=CourtResponse)
def get_court(
    court_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")
    return court


@router.get("/{court_id}/devices", response_model=list[DeviceResponse])
def list_court_devices(
    court_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")

    devices = (
        db.query(Device)
        .filter(Device.court_id == court_id)
        .order_by(Device.camera_index)
        .all()
    )
    return devices


@router.post("/{court_id}/rotate-key", response_model=CourtResponse)
def rotate_device_key(
    court_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")

    court.device_api_key = generate_device_api_key()
    db.commit()
    db.refresh(court)
    return court


@router.delete("/{court_id}", response_model=MessageResponse)
def deactivate_court(
    court_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    court = db.get(Court, court_id)
    if not court:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")

    court.is_active = False
    db.commit()
    return MessageResponse(message="Quadra desativada com sucesso")
