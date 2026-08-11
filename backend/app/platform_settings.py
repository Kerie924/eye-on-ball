from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import PlatformSettings


def ensure_platform_settings(db: Session) -> PlatformSettings:
    row = db.get(PlatformSettings, 1)
    if row:
        changed = False
        if row.platform_name != "Lance On":
            row.platform_name = "Lance On"
            changed = True
        if row.support_email and "olhonolance.com.br" in row.support_email:
            row.support_email = "suporte@lanceon.com.br"
            changed = True
        if changed:
            db.commit()
            db.refresh(row)
        return row

    row = PlatformSettings(
        id=1,
        platform_name="Lance On",
        support_email="suporte@lanceon.com.br",
        timezone="America/Sao_Paulo",
        language="pt-BR",
        storage_limit_tb=5.0,
        retention_hours=settings.recording_retention_hours,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
