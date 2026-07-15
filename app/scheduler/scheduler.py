"""Background job scheduler for appointment reminders."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import SessionLocal
from app.services.reminder_service import process_reminder_check

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


async def check_upcoming_appointments() -> None:
    """Scan for appointments due for reminder notifications."""
    if not settings.reminder_enabled:
        return

    db = SessionLocal()
    try:
        result = process_reminder_check(db)
        if result.total_sent:
            logger.info(
                "Reminder tick - checked=%s web=%s email=%s sms=%s",
                result.checked,
                result.sent_web,
                result.sent_email,
                result.sent_sms,
            )
    except Exception:
        logger.exception("Reminder check failed")
    finally:
        db.close()


def start_scheduler() -> None:
    """Register jobs and start the scheduler."""
    if not settings.reminder_enabled:
        logger.info("Reminder scheduler disabled via REMINDER_ENABLED=false")
        return

    scheduler.add_job(
        check_upcoming_appointments,
        trigger="interval",
        minutes=settings.reminder_check_interval_minutes,
        id="appointment_reminder_check",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started - reminder check every %s minute(s), "
        "windows at %sh and %sh before appointments",
        settings.reminder_check_interval_minutes,
        settings.reminder_hours_before,
        settings.reminder_followup_hours_before,
    )


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
