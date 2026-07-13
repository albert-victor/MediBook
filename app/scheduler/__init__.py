"""Scheduler package."""

from app.scheduler.scheduler import (
    check_upcoming_appointments,
    scheduler,
    shutdown_scheduler,
    start_scheduler,
)

__all__ = [
    "scheduler",
    "check_upcoming_appointments",
    "start_scheduler",
    "shutdown_scheduler",
]
