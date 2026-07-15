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
    static_asset_version: str = "20260715a"

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

    # SMS - KilaKona (server-side only)
    sms_reminders_enabled: bool = True
    # Send SMS for the 2h follow-up window (uses extra credits — keep false when low)
    sms_reminder_followup_enabled: bool = False
    sms_payment_enabled: bool = True
    # SMS when doctor approves/confirms (1 credit) — disable if credits are low
    sms_doctor_confirm_enabled: bool = True
    sms_api_url: str = (
        "https://messaging.kilakona.co.tz/api/v1/vendor/message/send"
    )
    sms_api_key: str | None = None
    sms_api_secret: str | None = None
    sms_sender_id: str | None = None
    sms_delivery_report_url: str | None = None
    sms_default_language: str = "sw"

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
