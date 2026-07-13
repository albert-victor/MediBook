"""Application configuration."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root (two levels up from this file: app/config -> app -> root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Central application settings loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "mediBook - Medical Appointment & Reminder System"
    brand_name: str = "mediBook"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-long-random-string"
    static_asset_version: str = "20260713g"

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # Database
    database_url: str = (
        f"sqlite:///{(BASE_DIR / 'data' / 'appointment.db').as_posix()}"
    )

    # Authentication (session-based)
    session_max_age: int = 60 * 60 * 24 * 14          # 14 days
    session_remember_max_age: int = 60 * 60 * 24 * 30   # 30 days

    # Scheduler / reminders
    reminder_check_interval_minutes: int = 15
    reminder_hours_before: int = 24
    reminder_followup_hours_before: int = 2
    reminder_enabled: bool = True

    # Email (simulated when SMTP is not configured)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "noreply@medibook.com"
    email_reminders_enabled: bool = True

    # Paths
    @property
    def base_dir(self) -> Path:
        return BASE_DIR

    @property
    def templates_dir(self) -> Path:
        return BASE_DIR / "templates"

    @property
    def static_dir(self) -> Path:
        return BASE_DIR / "static"

    @property
    def data_dir(self) -> Path:
        return BASE_DIR / "data"

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
