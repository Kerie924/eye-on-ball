from sqlalchemy import text

from app.constants import DEFAULT_CITIES
from app.database import SessionLocal, engine
from app.models import City, Court


def ensure_user_columns() -> None:
    """Add newer columns on existing Postgres databases."""
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS apple_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(128)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ",
        "ALTER TABLE court_access_requests ADD COLUMN IF NOT EXISTS play_started_at TIMESTAMPTZ",
        "ALTER TABLE court_access_requests ADD COLUMN IF NOT EXISTS play_ended_at TIMESTAMPTZ",
        """
        CREATE TABLE IF NOT EXISTS cities (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
        """,
        "ALTER TABLE courts ADD COLUMN IF NOT EXISTS city_id INTEGER",
        "ALTER TABLE courts DROP CONSTRAINT IF EXISTS courts_name_key",
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ix_courts_city_id_name
        ON courts (city_id, name)
        """,
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_apple_id ON users (apple_id)"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS feedback_reports (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    message TEXT NOT NULL,
                    status VARCHAR(16) NOT NULL DEFAULT 'new',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_feedback_reports_user_id ON feedback_reports (user_id)"
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_feedback_reports_status ON feedback_reports (status)"
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS feedback_images (
                    id SERIAL PRIMARY KEY,
                    report_id INTEGER NOT NULL REFERENCES feedback_reports(id) ON DELETE CASCADE,
                    file_key VARCHAR(512) NOT NULL,
                    content_type VARCHAR(128) NOT NULL DEFAULT 'image/jpeg',
                    created_at TIMESTAMPTZ DEFAULT NOW()
                )
                """
            )
        )
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_feedback_images_report_id ON feedback_images (report_id)"
            )
        )
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM pg_constraint WHERE conname = 'courts_city_id_fkey'
                    ) THEN
                        ALTER TABLE courts
                        ADD CONSTRAINT courts_city_id_fkey
                        FOREIGN KEY (city_id) REFERENCES cities(id);
                    END IF;
                END
                $$;
                """
            )
        )


def seed_default_cities() -> None:
    db = SessionLocal()
    try:
        existing = {row.name.lower() for row in db.query(City).all()}
        for name in DEFAULT_CITIES:
            if name.lower() not in existing:
                db.add(City(name=name, is_active=True))
        db.commit()

        fallback = (
            db.query(City)
            .filter(City.name == "Parauapebas", City.is_active.is_(True))
            .first()
        )
        if fallback is None:
            fallback = db.query(City).filter(City.is_active.is_(True)).order_by(City.name).first()
        if fallback is None:
            return

        unassigned = db.query(Court).filter(Court.city_id.is_(None)).all()
        for court in unassigned:
            court.city_id = fallback.id
        if unassigned:
            db.commit()
    finally:
        db.close()
