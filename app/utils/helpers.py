"""Shared utility helpers."""

from datetime import UTC, datetime


def utcnow() -> datetime:
    """Return the current UTC datetime (timezone-aware)."""
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    """Normalize naive datetimes from SQLite to UTC-aware."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt
