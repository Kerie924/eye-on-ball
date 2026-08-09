from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://olho:olho_dev@localhost:5432/olho_no_lance"
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7

    s3_endpoint_url: str = "http://localhost:9000"
    # Public URL phones/emulators can reach (LAN IP of MinIO). Falls back to s3_endpoint_url.
    s3_public_endpoint_url: str | None = None
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "olho-videos"
    s3_region: str = "us-east-1"

    recording_retention_hours: int = 48
    clip_duration_seconds: int = 30

    admin_email: str = "admin@olhonolance.com.br"
    admin_password: str = "change-me"
    admin_name: str = "Administrador"

    # Google OAuth client ID(s) used to verify ID tokens (comma-separated OK)
    google_client_id: str | None = None


    @property
    def google_client_ids(self) -> set[str]:
        if not self.google_client_id:
            return set()
        return {item.strip() for item in self.google_client_id.split(",") if item.strip()}


settings = Settings()
