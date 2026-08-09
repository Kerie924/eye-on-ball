from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PlatformSettings


def ensure_platform_settings(db: Session) -> PlatformSettings:
    row = db.get(PlatformSettings, 1)
    if row:
        return row

    row = PlatformSettings(
        id=1,
        platform_name="Olho no Lance",
        support_email="suporte@olhonolance.com.br",
        timezone="America/Sao_Paulo",
        language="pt-BR",
        storage_limit_tb=5.0,
        retention_hours=settings.recording_retention_hours,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
