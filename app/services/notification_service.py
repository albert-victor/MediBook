"""Notification creation and multi-channel dispatch."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import Appointment, Doctor, Notification, User
from app.models.enums import (
    NotificationChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from app.services import email_service
from app.services import sms_service
from app.services import sms_templates
from app.utils.helpers import ensure_utc, utcnow

logger = logging.getLogger(__name__)

CHANNEL_LABELS = {
    NotificationChannel.WEB.value: "Web",
    NotificationChannel.EMAIL.value: "Email",
    NotificationChannel.SMS.value: "SMS",
}


@dataclass(frozen=True)
class ReminderContent:
    """Structured reminder payload stored in notification history."""

    doctor_name: str
    department: str
    date_label: str
    time_label: str
    time_range: str
    message: str
    status: str
    status_label: str
    hours_before: int

    @property
    def title(self) -> str:
        if self.hours_before >= 24:
            return "Appointment reminder - 24 hours before"
        if self.hours_before >= 2:
            return "Appointment reminder - 2 hours before"
        return f"Appointment reminder - {self.hours_before}h before"

    def reminder_key(self) -> str:
        return f"{self.hours_before}h"


def _reminder_title(hours_before: int) -> str:
    if hours_before >= 24:
        return "Appointment reminder - 24 hours before"
    if hours_before >= 2:
        return "Appointment reminder - 2 hours before"
    return f"Appointment reminder - {hours_before}h before"


def reminder_already_sent(
    db: Session,
    appointment_id: int,
    hours_before: int,
    channel: str,
) -> bool:
    """Prevent duplicate reminders for the same appointment, window, and channel."""
    title = _reminder_title(hours_before)
    existing = db.scalar(
        select(Notification.id).where(
            Notification.appointment_id == appointment_id,
            Notification.notification_type == NotificationType.APPOINTMENT_REMINDER.value,
            Notification.channel == channel,
            Notification.title == title,
        )
    )
    return existing is not None


def create_notification(
    db: Session,
    *,
    user_id: int,
    appointment_id: int | None,
    notification_type: str,
    channel: str,
    title: str,
    message: str,
    delivery_status: str = NotificationDeliveryStatus.SENT.value,
    sent_at=None,
) -> Notification:
    now = utcnow()
    note = Notification(
        user_id=user_id,
        appointment_id=appointment_id,
        notification_type=notification_type,
        channel=channel,
        title=title,
        message=message,
        is_read=False,
        sent_at=sent_at if sent_at is not None else (
            now if delivery_status == NotificationDeliveryStatus.SENT.value else None
        ),
    )
    db.add(note)
    db.flush()
    return note


def dispatch_web_reminder(
    db: Session,
    patient: User,
    appointment: Appointment,
    content: ReminderContent,
) -> Notification | None:
    if reminder_already_sent(db, appointment.id, content.hours_before, NotificationChannel.WEB.value):
        return None

    return create_notification(
        db,
        user_id=patient.id,
        appointment_id=appointment.id,
        notification_type=NotificationType.APPOINTMENT_REMINDER.value,
        channel=NotificationChannel.WEB.value,
        title=content.title,
        message=content.message,
        delivery_status=NotificationDeliveryStatus.SENT.value,
    )


def dispatch_email_reminder(
    db: Session,
    patient: User,
    appointment: Appointment,
    content: ReminderContent,
) -> Notification | None:
    if reminder_already_sent(db, appointment.id, content.hours_before, NotificationChannel.EMAIL.value):
        return None

    email_body = (
        f"Dear {patient.first_name},\n\n"
        f"{content.message}\n\n"
        f"Doctor: {content.doctor_name}\n"
        f"Department: {content.department}\n"
        f"Date: {content.date_label}\n"
        f"Time: {content.time_range}\n"
        f"Status: {content.status_label}\n\n"
        f"- mediBook"
    )

    sent = email_service.send_email(
        to_email=patient.email,
        subject=content.title,
        body=email_body,
    )

    return create_notification(
        db,
        user_id=patient.id,
        appointment_id=appointment.id,
        notification_type=NotificationType.APPOINTMENT_REMINDER.value,
        channel=NotificationChannel.EMAIL.value,
        title=content.title,
        message=content.message,
        delivery_status=(
            NotificationDeliveryStatus.SENT.value
            if sent
            else NotificationDeliveryStatus.FAILED.value
        ),
    )


def dispatch_sms_reminder(
    db: Session,
    patient: User,
    appointment: Appointment,
    content: ReminderContent,
) -> Notification | None:
    """Send appointment reminder SMS via KilaKona and record delivery history."""
    from app.config import get_settings

    settings = get_settings()
    if not settings.sms_reminders_enabled:
        return None

    # Follow-up window (default 2h) - off by default to conserve SMS credits
    if content.hours_before < settings.reminder_hours_before:
        if not settings.sms_reminder_followup_enabled:
            return None

    if reminder_already_sent(db, appointment.id, content.hours_before, NotificationChannel.SMS.value):
        return None

    if not patient.phone:
        logger.info(
            "SMS skipped - patient %s has no phone (appointment %s)",
            patient.id,
            appointment.id,
        )
        return None

    # Credit guard: day-before SMS only while still ~1 day out (not same-day leftovers)
    hours_left = (
        ensure_utc(appointment.scheduled_start) - utcnow()
    ).total_seconds() / 3600
    if content.hours_before >= settings.reminder_hours_before:
        min_left = max(settings.reminder_hours_before - 4, 12)
        if hours_left < min_left:
            logger.info(
                "SMS reminder skipped for appointment %s - already closer than %sh (%.1fh left)",
                appointment.id,
                min_left,
                hours_left,
            )
            return None

    sms_body = sms_templates.format_sms_reminder(
        patient,
        doctor_name=content.doctor_name,
        department=content.department,
        hours_before=content.hours_before,
        scheduled_start=appointment.scheduled_start,
    )
    sent = sms_service.send_sms(
        to_phone=patient.phone,
        message=sms_body,
    )

    if not sms_service.is_sms_configured():
        delivery = NotificationDeliveryStatus.SKIPPED.value
        sent_at = None
    elif sent:
        delivery = NotificationDeliveryStatus.SENT.value
        sent_at = utcnow()
    else:
        delivery = NotificationDeliveryStatus.FAILED.value
        sent_at = None

    return create_notification(
        db,
        user_id=patient.id,
        appointment_id=appointment.id,
        notification_type=NotificationType.APPOINTMENT_REMINDER.value,
        channel=NotificationChannel.SMS.value,
        title=content.title,
        message=sms_body,
        delivery_status=delivery,
        sent_at=sent_at,
    )


def get_delivery_status(note: Notification) -> str:
    if note.channel == NotificationChannel.SMS.value and note.sent_at is None:
        return NotificationDeliveryStatus.SKIPPED.value
    if note.sent_at is not None:
        return NotificationDeliveryStatus.SENT.value
    return NotificationDeliveryStatus.PENDING.value


def serialize_notification_with_appointment(
    db: Session,
    note: Notification,
) -> dict:
    """Enrich a notification with appointment details when available."""
    delivery = get_delivery_status(note)
    base = {
        "id": note.id,
        "type": note.notification_type,
        "title": note.title,
        "message": note.message,
        "is_read": note.is_read,
        "created_at": ensure_utc(note.created_at).isoformat(),
        "appointment_id": note.appointment_id,
        "channel": note.channel,
        "channel_label": CHANNEL_LABELS.get(note.channel, note.channel),
        "delivery_status": delivery,
        "delivery_status_label": delivery.replace("_", " ").title(),
        "doctor_name": None,
        "department": None,
        "appointment_date": None,
        "appointment_time": None,
        "appointment_status": None,
        "appointment_status_label": None,
    }

    if not note.appointment_id:
        return base

    appointment = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
        )
        .where(Appointment.id == note.appointment_id)
    )
    if not appointment:
        return base

    doctor = appointment.doctor
    start = ensure_utc(appointment.scheduled_start)
    end = ensure_utc(appointment.scheduled_end)
    name = doctor.user.full_name if doctor and doctor.user else "Unknown"
    if doctor and not name.startswith("Dr."):
        name = f"Dr. {name}"
    spec = doctor.specialization.name if doctor and doctor.specialization else "General"

    from app.services.appointment_service import STATUS_LABELS

    base.update({
        "doctor_name": name,
        "department": spec,
        "appointment_date": start.strftime("%A, %d %B %Y"),
        "appointment_time": start.strftime("%H:%M"),
        "appointment_status": appointment.status,
        "appointment_status_label": STATUS_LABELS.get(
            appointment.status, appointment.status.title()
        ),
    })
    return base
