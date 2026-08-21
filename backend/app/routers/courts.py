from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.constants import MAX_CAMERAS_PER_COURT
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import City, Court, Device, User, UserRole
from app.schemas import CourtCreate, CourtResponse, CourtUpdate, DeviceResponse, MessageResponse
from app.security import generate_device_api_key

router = APIRouter(prefix="/courts", tags=["courts"])


def _court_response(court: Court, include_key: bool) -> CourtResponse:
    return CourtResponse(
        id=court.id,
        name=court.name,
        city_id=court.city_id,
        city_name=court.city.name if court.city else None,
        address=court.address,
        is_active=court.is_active,
        created_at=court.created_at,
        device_api_key=court.device_api_key if include_key else None,
    )


def _ensure_camera_devices(db: Session, court_id: int, camera_count: int) -> None:
    existing = {
        device.camera_index
        for device in db.query(Device).filter(Device.court_id == court_id).all()
    }
    for camera_index in range(1, camera_count + 1):
        if camera_index in existing:
            continue
        db.add(
            Device(
                court_id=court_id,
                camera_index=camera_index,
                name=f"Camera {camera_index}",
            )
        )


def _require_city(db: Session, city_id: int) -> City:
    city = db.get(City, city_id)
    if not city or not city.is_active:
        raise HTTPException(status_code=400, detail="Cidade invalida ou desativada")
    return city


@router.post("", response_model=CourtResponse, status_code=status.HTTP_201_CREATED)
def create_court(
    payload: CourtCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    _require_city(db, payload.city_id)
    existing = (
        db.query(Court)
        .filter(Court.city_id == payload.city_id, Court.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ja existe uma quadra com este nome nesta cidade",
        )

    court = Court(
        name=payload.name,
        city_id=payload.city_id,
        address=payload.address,
        device_api_key=generate_device_api_key(),
    )
    db.add(court)
    db.flush()

    _ensure_camera_devices(db, court.id, payload.camera_count)

    db.commit()
    court = (
        db.query(Court)
        .options(joinedload(Court.city))
        .filter(Court.id == court.id)
        .first()
    )
    return _court_response(court, include_key=True)


@router.get("", response_model=list[CourtResponse])
def list_courts(
    city_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        db.query(Court)
        .options(joinedload(Court.city))
        .filter(Court.is_active.is_(True))
        .order_by(Court.name)
    )
    if city_id is not None:
        query = query.filter(Court.city_id == city_id)

    courts = query.all()
    include_key = current_user.role == UserRole.admin
    return [_court_response(court, include_key=include_key) for court in courts]


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

    next_city_id = payload.city_id if payload.city_id is not None else court.city_id
    next_name = payload.name if payload.name else court.name

    if payload.city_id is not None:
        _require_city(db, payload.city_id)
        court.city_id = payload.city_id

    if payload.name and payload.name != court.name:
        court.name = payload.name

    clash = (
        db.query(Court)
        .filter(
            Court.city_id == next_city_id,
            Court.name == next_name,
            Court.id != court.id,
        )
        .first()
    )
    if clash:
        raise HTTPException(
            status_code=400,
            detail="Ja existe uma quadra com este nome nesta cidade",
        )

    if payload.address is not None:
        court.address = payload.address

    if payload.camera_count is not None:
        current = (
            db.query(Device)
            .filter(Device.court_id == court.id)
            .count()
        )
        if payload.camera_count < current:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Nao e possivel reduzir o numero de cameras ({current} cadastradas). "
                    f"O limite e {MAX_CAMERAS_PER_COURT}."
                ),
            )
        _ensure_camera_devices(db, court.id, payload.camera_count)

    db.commit()
    court = (
        db.query(Court)
        .options(joinedload(Court.city))
        .filter(Court.id == court_id)
        .first()
    )
    return _court_response(court, include_key=True)


@router.get("/{court_id}", response_model=CourtResponse)
def get_court(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    court = (
        db.query(Court)
        .options(joinedload(Court.city))
        .filter(Court.id == court_id)
        .first()
    )
    if not court:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")
    return _court_response(court, include_key=current_user.role == UserRole.admin)


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
    court = (
        db.query(Court)
        .options(joinedload(Court.city))
        .filter(Court.id == court_id)
        .first()
    )
    return _court_response(court, include_key=True)


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
