from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Recording
from app.storage import delete_file


def cleanup_expired_recordings() -> None:
    db: Session = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        expired = db.query(Recording).filter(Recording.expires_at <= now).all()
        for recording in expired:
            try:
                delete_file(recording.file_key)
            except Exception:
                pass
            # Keep the database row so admin Gravacoes can list Expirado.
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_expired_recordings, "interval", hours=1)
    scheduler.start()
    return scheduler
