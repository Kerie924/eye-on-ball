from sqlalchemy import text

from app.database import engine


def ensure_user_columns() -> None:
    """Add newer columns on existing Postgres databases."""
    statements = [
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url TEXT",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(128)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expires TIMESTAMPTZ",
        "ALTER TABLE court_access_requests ADD COLUMN IF NOT EXISTS play_started_at TIMESTAMPTZ",
        "ALTER TABLE court_access_requests ADD COLUMN IF NOT EXISTS play_ended_at TIMESTAMPTZ",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id)"
            )
        )
