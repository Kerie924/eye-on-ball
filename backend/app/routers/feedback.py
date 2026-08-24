import logging
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
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
    message: str = Form(...),
    images: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    text = (message or "").strip()
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
    uploads = [item for item in images if item.filename]
    if len(uploads) > MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Envie no maximo {MAX_IMAGES} fotos.",
        )

    report = FeedbackReport(user_id=current_user.id, message=text, status="new")
    db.add(report)
    db.flush()

    image_urls: list[str] = []
    for upload in uploads:
        content_type = (upload.content_type or "image/jpeg").lower()
        if content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=400,
                detail="Envie apenas imagens (JPG, PNG, WEBP ou HEIC).",
            )
        data = await upload.read()
        if not data:
            continue
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
