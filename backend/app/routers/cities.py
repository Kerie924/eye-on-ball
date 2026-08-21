from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models import City, Court, User, UserRole
from app.schemas import CityCreate, CityResponse, CityUpdate, MessageResponse

router = APIRouter(prefix="/cities", tags=["cities"])


def _city_response(city: City, court_count: int) -> CityResponse:
    return CityResponse(
        id=city.id,
        name=city.name,
        is_active=city.is_active,
        created_at=city.created_at,
        court_count=court_count,
    )


@router.get("", response_model=list[CityResponse])
def list_cities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_inactive: bool = False,
):
    query = db.query(City)
    if current_user.role != UserRole.admin or not include_inactive:
        query = query.filter(City.is_active.is_(True))
    cities = query.order_by(City.name).all()
    count_rows = (
        db.query(Court.city_id, func.count(Court.id))
        .filter(Court.is_active.is_(True))
        .group_by(Court.city_id)
        .all()
    )
    count_map = {city_id: count for city_id, count in count_rows if city_id is not None}
    return [_city_response(city, count_map.get(city.id, 0)) for city in cities]


@router.post("", response_model=CityResponse, status_code=status.HTTP_201_CREATED)
def create_city(
    payload: CityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    name = payload.name.strip()
    existing = db.query(City).filter(City.name.ilike(name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ja existe uma cidade com este nome")
    city = City(name=name, is_active=True)
    db.add(city)
    db.commit()
    db.refresh(city)
    return _city_response(city, 0)


@router.patch("/{city_id}", response_model=CityResponse)
def update_city(
    city_id: int,
    payload: CityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    city = db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="Cidade nao encontrada")

    if payload.name:
        name = payload.name.strip()
        clash = (
            db.query(City)
            .filter(City.name.ilike(name), City.id != city_id)
            .first()
        )
        if clash:
            raise HTTPException(status_code=400, detail="Ja existe uma cidade com este nome")
        city.name = name

    if payload.is_active is not None:
        city.is_active = payload.is_active

    db.commit()
    db.refresh(city)
    court_count = (
        db.query(func.count(Court.id))
        .filter(Court.city_id == city.id, Court.is_active.is_(True))
        .scalar()
        or 0
    )
    return _city_response(city, court_count)


@router.delete("/{city_id}", response_model=MessageResponse)
def deactivate_city(
    city_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    city = db.get(City, city_id)
    if not city:
        raise HTTPException(status_code=404, detail="Cidade nao encontrada")
    city.is_active = False
    db.commit()
    return MessageResponse(message="Cidade desativada com sucesso")
