from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import (
    get_current_user,
    require_admin,
    require_athlete,
)
from app.models import (
    AccessRequestStatus,
    Court,
    CourtAccess,
    CourtAccessRequest,
    User,
    UserRole,
)
from app.schemas import (
    CourtAccessRequestCreate,
    CourtAccessRequestResponse,
    CourtAccessResponse,
    CourtResponse,
    MessageResponse,
)

router = APIRouter(tags=["access"])

MAX_PLAY_WINDOW = timedelta(hours=6)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@router.post(
    "/access-requests",
    response_model=CourtAccessRequestResponse,
    status_code=status.HTTP_201_CREATED,
)
def request_court_access(
    payload: CourtAccessRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_athlete),
):
    court = db.get(Court, payload.court_id)
    if not court or not court.is_active:
        raise HTTPException(status_code=404, detail="Quadra nao encontrada")

    started = _as_utc(payload.play_started_at)
    ended = _as_utc(payload.play_ended_at)
    if ended <= started:
        raise HTTPException(
            status_code=400,
            detail="O horario final deve ser depois do horario inicial",
        )
    if ended - started > MAX_PLAY_WINDOW:
        raise HTTPException(
            status_code=400,
            detail="O periodo de jogo pode ter no maximo 6 horas",
        )

    pending = (
        db.query(CourtAccessRequest)
        .filter(
            CourtAccessRequest.user_id == current_user.id,
            CourtAccessRequest.court_id == payload.court_id,
            CourtAccessRequest.status == AccessRequestStatus.pending,
        )
        .first()
    )
    if pending:
        raise HTTPException(
            status_code=400,
            detail="Ja existe uma solicitacao pendente para esta quadra",
        )

    request = CourtAccessRequest(
        user_id=current_user.id,
        court_id=payload.court_id,
        play_started_at=started,
        play_ended_at=ended,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


@router.get("/access-requests/mine", response_model=list[CourtAccessRequestResponse])
def my_access_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_athlete),
):
    requests = (
        db.query(CourtAccessRequest)
        .options(joinedload(CourtAccessRequest.court))
        .filter(CourtAccessRequest.user_id == current_user.id)
        .order_by(CourtAccessRequest.created_at.desc())
        .all()
    )
    return requests


@router.get("/access-requests", response_model=list[CourtAccessRequestResponse])
def list_access_requests(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    requests = (
        db.query(CourtAccessRequest)
        .options(
            joinedload(CourtAccessRequest.user),
            joinedload(CourtAccessRequest.court),
        )
        .filter(CourtAccessRequest.status == AccessRequestStatus.pending)
        .order_by(CourtAccessRequest.created_at.asc())
        .all()
    )
    return requests


@router.post("/access-requests/{request_id}/approve", response_model=MessageResponse)
def approve_access_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    request = db.get(CourtAccessRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")
    if request.status != AccessRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Solicitacao ja foi revisada")

    existing_access = (
        db.query(CourtAccess)
        .filter(
            CourtAccess.user_id == request.user_id,
            CourtAccess.court_id == request.court_id,
        )
        .first()
    )
    if not existing_access:
        db.add(
            CourtAccess(
                user_id=request.user_id,
                court_id=request.court_id,
                granted_by_id=admin.id,
            )
        )

    request.status = AccessRequestStatus.approved
    request.reviewed_at = datetime.now(timezone.utc)
    request.reviewed_by_id = admin.id
    db.commit()
    return MessageResponse(message="Acesso aprovado com sucesso")


@router.post("/access-requests/{request_id}/reject", response_model=MessageResponse)
def reject_access_request(
    request_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    request = db.get(CourtAccessRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitacao nao encontrada")
    if request.status != AccessRequestStatus.pending:
        raise HTTPException(status_code=400, detail="Solicitacao ja foi revisada")

    request.status = AccessRequestStatus.rejected
    request.reviewed_at = datetime.now(timezone.utc)
    request.reviewed_by_id = admin.id
    db.commit()
    return MessageResponse(message="Solicitacao rejeitada")


@router.get("/access/mine", response_model=list[CourtAccessResponse])
def my_court_access(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Admins and approved scouts can see all active courts.
    if current_user.role == UserRole.admin or (
        current_user.role == UserRole.scout and current_user.is_approved
    ):
        courts = db.query(Court).filter(Court.is_active.is_(True)).order_by(Court.name).all()
        now = datetime.now(timezone.utc)
        return [
            CourtAccessResponse(
                id=0,
                user_id=current_user.id,
                court_id=court.id,
                granted_at=now,
                court=CourtResponse(
                    id=court.id,
                    name=court.name,
                    address=court.address,
                    is_active=court.is_active,
                    created_at=court.created_at,
                ),
            )
            for court in courts
        ]

    accesses = (
        db.query(CourtAccess)
        .options(joinedload(CourtAccess.court))
        .filter(CourtAccess.user_id == current_user.id)
        .order_by(CourtAccess.granted_at.desc())
        .all()
    )
    return accesses
