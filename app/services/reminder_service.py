"""Appointment reminder engine - scans upcoming visits and dispatches notifications."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import Appointment, Doctor, User
from app.models.enums import AppointmentStatus
from app.services import notification_service as notify
from app.services.appointment_service import STATUS_LABELS
from app.services.notification_service import ReminderContent
from app.utils.helpers import ensure_utc, utcnow

logger = logging.getLogger(__name__)
settings = get_settings()

ACTIVE_STATUSES = (
    AppointmentStatus.PENDING.value,
    AppointmentStatus.SCHEDULED.value,
    AppointmentStatus.CONFIRMED.value,
)


@dataclass
class ReminderCheckResult:
    checked: int = 0
    sent_web: int = 0
    sent_email: int = 0
    sent_sms: int = 0
    skipped: int = 0
    errors: int = 0

    @property
    def total_sent(self) -> int:
        return self.sent_web + self.sent_email + self.sent_sms


def _display_name(doctor: Doctor) -> str:
    name = doctor.user.full_name if doctor.user else f"Doctor #{doctor.id}"
    if not name.startswith("Dr."):
        return f"Dr. {name}"
    return name


def _reminder_windows() -> list[int]:
    windows = [settings.reminder_hours_before]
    if settings.reminder_followup_hours_before not in windows:
        windows.append(settings.reminder_followup_hours_before)
    return sorted(windows, reverse=True)


def _hours_until(appointment: Appointment, now) -> float:
    delta = ensure_utc(appointment.scheduled_start) - now
    return delta.total_seconds() / 3600


def is_due_for_reminder(appointment: Appointment, hours_before: int, now) -> bool:
    """True when the appointment is in the future and within the reminder window."""
    hours_left = _hours_until(appointment, now)
    if hours_left <= 0:
        return False
    return hours_left <= hours_before


def build_reminder_content(appointment: Appointment, hours_before: int) -> ReminderContent:
    doctor = appointment.doctor
    start = ensure_utc(appointment.scheduled_start)
    end = ensure_utc(appointment.scheduled_end)
    spec = doctor.specialization.name if doctor and doctor.specialization else "General"
    doctor_name = _display_name(doctor) if doctor else "your doctor"
    status_label = STATUS_LABELS.get(appointment.status, appointment.status.title())

    if hours_before >= 24:
        timing = "in 24 hours"
    elif hours_before >= 2:
        timing = "in 2 hours"
    else:
        timing = f"in {hours_before} hours"

    message = (
        f"Your visit with {doctor_name} ({spec}) is {timing} on "
        f"{start.strftime('%A, %d %B %Y')} at {start.strftime('%H:%M')}. "
        f"Please arrive 10 minutes early. Appointment status: {status_label}."
    )

    return ReminderContent(
        doctor_name=doctor_name,
        department=spec,
        date_label=start.strftime("%A, %d %B %Y"),
        time_label=start.strftime("%H:%M"),
        time_range=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
        message=message,
        status=appointment.status,
        status_label=status_label,
        hours_before=hours_before,
    )


def _load_upcoming_appointments(db: Session, now) -> list[Appointment]:
    max_hours = max(_reminder_windows())
    horizon = now + timedelta(hours=max_hours + 1)

    return list(
        db.scalars(
            select(Appointment)
            .options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor).joinedload(Doctor.user),
                joinedload(Appointment.doctor).joinedload(Doctor.specialization),
            )
            .where(
                Appointment.scheduled_start > now,
                Appointment.scheduled_start <= horizon,
                Appointment.status.in_(ACTIVE_STATUSES),
            )
            .order_by(Appointment.scheduled_start.asc())
        ).unique().all()
    )


def _dispatch_reminder(
    db: Session,
    appointment: Appointment,
    content: ReminderContent,
    result: ReminderCheckResult,
) -> None:
    patient = appointment.patient
    if not patient:
        result.skipped += 1
        return

    web = notify.dispatch_web_reminder(db, patient, appointment, content)
    if web:
        result.sent_web += 1

    email = notify.dispatch_email_reminder(db, patient, appointment, content)
    if email:
        result.sent_email += 1

    sms = notify.dispatch_sms_reminder(db, patient, appointment, content)
    if sms:
        result.sent_sms += 1


def process_reminder_check(db: Session) -> ReminderCheckResult:
    """Scan upcoming appointments and create reminder notifications."""
    result = ReminderCheckResult()

    if not settings.reminder_enabled:
        logger.debug("Reminder engine disabled")
        return result

    now = utcnow()
    appointments = _load_upcoming_appointments(db, now)
    result.checked = len(appointments)

    for appointment in appointments:
        for hours_before in _reminder_windows():
            if not is_due_for_reminder(appointment, hours_before, now):
                continue

            content = build_reminder_content(appointment, hours_before)
            try:
                _dispatch_reminder(db, appointment, content, result)
            except Exception:
                logger.exception(
                    "Failed to dispatch reminder for appointment %s (%sh)",
                    appointment.id,
                    hours_before,
                )
                result.errors += 1

    if result.total_sent:
        db.commit()
        logger.info(
            "Reminder check complete - web=%s email=%s sms=%s errors=%s",
            result.sent_web,
            result.sent_email,
            result.sent_sms,
            result.errors,
        )
    else:
        db.rollback()
        logger.debug(
            "Reminder check complete - no new reminders (checked %s appointments)",
            result.checked,
        )

    return result
