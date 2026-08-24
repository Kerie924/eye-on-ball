import base64
import logging
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.emailer import email_configured, send_feedback_email
from app.models import FeedbackImage, FeedbackReport, PlatformSettings, User
from app.platform_settings import ensure_platform_settings
from app.schemas import FeedbackImageResponse, FeedbackReportResponse, FeedbackSubmitResponse
from app.storage import generate_download_url, upload_file

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])

MAX_IMAGES = 4
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MIN_MESSAGE = 10
MAX_MESSAGE = 2000
ALLOWED_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
}


def _normalize_content_type(content_type: str | None) -> str:
    value = (content_type or "image/jpeg").lower().split(";")[0].strip()
    if value in {"application/octet-stream", "binary/octet-stream", "image"}:
        return "image/jpeg"
    return value


def _decode_data_url(raw: str) -> bytes:
    payload = raw.strip()
    if payload.startswith("data:") and "," in payload:
        payload = payload.split(",", 1)[1]
    return base64.b64decode(payload)


async def _read_payload(request: Request) -> tuple[str, list[tuple[str, bytes]]]:
    header = (request.headers.get("content-type") or "").lower()
    files: list[tuple[str, bytes]] = []

    if "application/json" in header:
        payload = await request.json()
        text = str(payload.get("message") or "").strip()
        for item in payload.get("images") or []:
            if not isinstance(item, dict):
                continue
            raw = item.get("data")
            if not isinstance(raw, str) or not raw.strip():
                continue
            try:
                data = _decode_data_url(raw)
            except Exception as exc:
                raise HTTPException(status_code=400, detail="Foto invalida.") from exc
            content_type = _normalize_content_type(item.get("content_type"))
            files.append((content_type, data))
        return text, files

    form = await request.form()
    raw_message = form.get("message")
    text = raw_message.strip() if isinstance(raw_message, str) else ""
    for key, item in form.multi_items():
        if key != "images" or not isinstance(item, UploadFile):
            continue
        data = await item.read()
        if not data:
            continue
        files.append((_normalize_content_type(item.content_type), data))
    return text, files


def _ext_for_type(content_type: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
        "image/heif": ".heif",
    }
    return mapping.get(content_type, ".jpg")


def _to_response(report: FeedbackReport) -> FeedbackReportResponse:
    return FeedbackReportResponse(
        id=report.id,
        user_id=report.user_id,
        user_name=report.user.full_name if report.user else None,
        user_email=report.user.email if report.user else None,
        message=report.message,
        status=report.status,
        created_at=report.created_at,
        images=[
            FeedbackImageResponse(
                id=image.id,
                url=generate_download_url(
                    image.file_key,
                    filename=f"relato-{report.id}-{image.id}",
                ),
            )
            for image in report.images
        ],
    )


@router.post("/feedback", response_model=FeedbackSubmitResponse, status_code=201)
async def submit_feedback(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text, files = await _read_payload(request)
    if len(text) < MIN_MESSAGE:
        raise HTTPException(
            status_code=400,
            detail=f"Escreva pelo menos {MIN_MESSAGE} caracteres.",
        )
    if len(text) > MAX_MESSAGE:
        raise HTTPException(
            status_code=400,
            detail=f"A mensagem pode ter no maximo {MAX_MESSAGE} caracteres.",
        )
    if len(files) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Envie no maximo {MAX_IMAGES} fotos.",
        )

    report = FeedbackReport(user_id=current_user.id, message=text, status="new")
    db.add(report)
    db.flush()

    image_urls: list[str] = []
    for content_type, data in files:
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Envie apenas imagens (JPG, PNG, WEBP ou HEIC).",
            )
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=400,
                detail="Cada foto pode ter no maximo 8 MB.",
            )
        key = f"feedback/{report.id}/{uuid4().hex}{_ext_for_type(content_type)}"
        upload_file(BytesIO(data), key, content_type=content_type)
        db.add(
            FeedbackImage(
                report_id=report.id,
                file_key=key,
                content_type=content_type,
            )
        )
        image_urls.append(generate_download_url(key, filename=f"relato-{report.id}"))

    db.commit()
    db.refresh(report)

    if email_configured():
        settings_row = db.get(PlatformSettings, 1) or ensure_platform_settings(db)
        try:
            send_feedback_email(
                settings_row.support_email,
                current_user.full_name,
                current_user.email,
                text,
                image_urls,
            )
        except Exception:
            logger.exception("Failed to email feedback report %s", report.id)

    return FeedbackSubmitResponse(
        id=report.id,
        message="Relato enviado. Obrigado pelo feedback.",
    )


@router.get("/admin/feedback", response_model=list[FeedbackReportResponse])
def list_feedback(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    reports = (
        db.query(FeedbackReport)
        .options(joinedload(FeedbackReport.user), joinedload(FeedbackReport.images))
        .order_by(FeedbackReport.created_at.desc())
        .all()
    )
    return [_to_response(report) for report in reports]


@router.patch("/admin/feedback/{report_id}", response_model=FeedbackReportResponse)
def mark_feedback_read(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    report = (
        db.query(FeedbackReport)
        .options(joinedload(FeedbackReport.user), joinedload(FeedbackReport.images))
        .filter(FeedbackReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Relato nao encontrado")
    report.status = "read"
    db.commit()
    db.refresh(report)
    return _to_response(report)
