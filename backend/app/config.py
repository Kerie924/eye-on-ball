from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://lanceon:lanceon_dev@localhost:5432/lance_on"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7

    # MinIO/local: http://localhost:9000 — AWS S3: leave empty (uses regional AWS endpoint)
    s3_endpoint_url: str | None = "http://localhost:9000"
    # Public URL phones can reach (LAN MinIO). Not needed for real AWS S3 presigned URLs.
    s3_public_endpoint_url: str | None = None
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "lanceon-videos"
    s3_region: str = "us-east-1"

    recording_retention_hours: int = 48
    clip_duration_seconds: int = 30

    admin_email: str = "admin@lanceon.com.br"
    admin_password: str = "change-me"
    admin_name: str = "Administrador"

    # Google OAuth client ID(s) used to verify ID tokens (comma-separated OK)
    google_client_id: str | None = None
    # Firebase project ID used to verify Authentication ID tokens
    firebase_project_id: str | None = None

    public_api_url: str = "https://api.lanceonpara.com.br"

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    ses_from_email: str | None = None


    @property
    def google_client_ids(self) -> set[str]:
        if not self.google_client_id:
            return set()
        return {item.strip() for item in self.google_client_id.split(",") if item.strip()}


settings = Settings()
