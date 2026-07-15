"""Doctor dashboard - own appointments, patients, and actions."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.config import get_settings
from app.models import (
    Appointment,
    AppointmentStatusHistory,
    Doctor,
    Notification,
    Payment,
    User,
)
from app.models.enums import (
    AppointmentStatus,
    NotificationChannel,
    NotificationType,
    PaymentStatus,
)
from app.schemas.doctor_dashboard import (
    DoctorActivityItem,
    DoctorAppointmentItem,
    DoctorCalendarDay,
    DoctorDashboardOverview,
    DoctorDashboardStats,
    DoctorPatientBrief,
    DoctorPatientDetail,
)
from app.services import sms_service
from app.services import sms_templates
from app.services.appointment_service import STATUS_LABELS, release_availability_for_appointment
from app.utils.exceptions import ConflictError, NotFoundError
from app.utils.helpers import ensure_utc, utcnow

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = (
    AppointmentStatus.PENDING.value,
    AppointmentStatus.SCHEDULED.value,
    AppointmentStatus.CONFIRMED.value,
)


def _greeting() -> str:
    hour = utcnow().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _initials(name: str) -> str:
    parts = name.split()
    return "".join(p[0] for p in parts[:2]).upper()


def _doctor_for_user(db: Session, user: User) -> Doctor:
    doctor = db.scalar(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.user_id == user.id)
    )
    if not doctor:
        raise NotFoundError("Doctor profile not found")
    return doctor


def _display_doctor_name(doctor: Doctor) -> str:
    name = doctor.user.full_name if doctor.user else f"Doctor #{doctor.id}"
    if not name.startswith("Dr."):
        return f"Dr. {name}"
    return name


def _appointment_query(doctor_id: int):
    return (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.payment),
        )
        .where(Appointment.doctor_id == doctor_id)
    )


def _serialize_appointment(appt: Appointment) -> DoctorAppointmentItem:
    patient = appt.patient
    name = patient.full_name if patient else "Unknown"
    start = ensure_utc(appt.scheduled_start)
    end = ensure_utc(appt.scheduled_end)
    return DoctorAppointmentItem(
        id=appt.id,
        patient_id=appt.patient_id,
        patient_name=name,
        patient_initials=_initials(name),
        patient_phone=patient.phone if patient else None,
        patient_email=patient.email if patient else "",
        scheduled_start=start.isoformat(),
        scheduled_end=end.isoformat(),
        date_label=start.strftime("%A, %d %B %Y"),
        time_range=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
        status=appt.status,
        status_label=STATUS_LABELS.get(appt.status, appt.status.title()),
        patient_notes=appt.patient_notes,
        payment_status=appt.payment.status if appt.payment else None,
        cancellation_reason=appt.cancellation_reason,
    )


def get_overview(db: Session, user: User) -> DoctorDashboardOverview:
    doctor = _doctor_for_user(db, user)
    now = utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    today_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_start >= today_start,
            Appointment.scheduled_start < today_end,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    ) or 0

    upcoming = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_start > now,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    ) or 0

    completed = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.status == AppointmentStatus.COMPLETED.value,
        )
    ) or 0

    cancelled = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.status == AppointmentStatus.CANCELLED.value,
        )
    ) or 0

    total_patients = db.scalar(
        select(func.count(func.distinct(Appointment.patient_id))).where(
            Appointment.doctor_id == doctor.id,
        )
    ) or 0

    pending = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.status.in_([
                AppointmentStatus.PENDING.value,
                AppointmentStatus.SCHEDULED.value,
            ]),
            Appointment.scheduled_start > now,
        )
    ) or 0

    spec = doctor.specialization.name if doctor.specialization else "General"

    return DoctorDashboardOverview(
        greeting=_greeting(),
        doctor_name=_display_doctor_name(doctor),
        specialization=spec,
        hospital=doctor.hospital_name,
        stats=DoctorDashboardStats(
            today=today_count,
            upcoming=upcoming,
            completed=completed,
            cancelled=cancelled,
            total_patients=total_patients,
            pending_approval=pending,
        ),
        profile_url=f"/doctors/{doctor.id}",
    )


def list_appointments(
    db: Session,
    user: User,
    *,
    q: str | None = None,
    date_filter: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[DoctorAppointmentItem]:
    doctor = _doctor_for_user(db, user)
    now = utcnow()
    stmt = _appointment_query(doctor.id)

    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.join(User, Appointment.patient_id == User.id).where(
            or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
                User.phone.ilike(term),
            )
        )

    if date_filter:
        try:
            day = date.fromisoformat(date_filter)
        except ValueError as exc:
            raise NotFoundError("Invalid date format") from exc
        day_start = datetime.combine(day, time.min, tzinfo=now.tzinfo)
        day_end = day_start + timedelta(days=1)
        stmt = stmt.where(
            Appointment.scheduled_start >= day_start,
            Appointment.scheduled_start < day_end,
        )

    if status_filter == "today":
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        stmt = stmt.where(
            Appointment.scheduled_start >= today_start,
            Appointment.scheduled_start < today_end,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    elif status_filter == "upcoming":
        stmt = stmt.where(
            Appointment.scheduled_start > now,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    elif status_filter == "completed":
        stmt = stmt.where(Appointment.status == AppointmentStatus.COMPLETED.value)
    elif status_filter == "cancelled":
        stmt = stmt.where(Appointment.status == AppointmentStatus.CANCELLED.value)
    elif status_filter == "pending":
        stmt = stmt.where(
            Appointment.status.in_([
                AppointmentStatus.PENDING.value,
                AppointmentStatus.SCHEDULED.value,
            ]),
            Appointment.scheduled_start > now,
        )

    appts = db.scalars(
        stmt.order_by(Appointment.scheduled_start.desc()).limit(limit)
    ).unique().all()
    return [_serialize_appointment(a) for a in appts]


def get_today_appointments(db: Session, user: User) -> list[DoctorAppointmentItem]:
    return list_appointments(db, user, status_filter="today", limit=20)


def get_appointment(db: Session, user: User, appointment_id: int) -> DoctorAppointmentItem:
    doctor = _doctor_for_user(db, user)
    appt = db.scalar(
        _appointment_query(doctor.id).where(Appointment.id == appointment_id)
    )
    if not appt:
        raise NotFoundError("Appointment not found")
    return _serialize_appointment(appt)


def list_patients(db: Session, user: User, limit: int = 12) -> list[DoctorPatientBrief]:
    doctor = _doctor_for_user(db, user)

    rows = db.execute(
        select(
            User.id,
            User.first_name,
            User.last_name,
            User.email,
            User.phone,
            func.count(Appointment.id),
            func.max(Appointment.scheduled_start),
        )
        .join(Appointment, Appointment.patient_id == User.id)
        .where(Appointment.doctor_id == doctor.id)
        .group_by(User.id)
        .order_by(func.max(Appointment.scheduled_start).desc())
        .limit(limit)
    ).all()

    return [
        DoctorPatientBrief(
            id=row[0],
            name=f"{row[1]} {row[2]}",
            initials=_initials(f"{row[1]} {row[2]}"),
            phone=row[4],
            email=row[3],
            total_visits=row[5] or 0,
            last_visit=ensure_utc(row[6]).isoformat() if row[6] else None,
        )
        for row in rows
    ]


def get_patient_detail(db: Session, user: User, patient_id: int) -> DoctorPatientDetail:
    doctor = _doctor_for_user(db, user)
    patient = db.get(User, patient_id)
    if not patient:
        raise NotFoundError("Patient not found")

    has_visit = db.scalar(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_id,
        ).limit(1)
    )
    if not has_visit:
        raise NotFoundError("Patient not found")

    now = utcnow()
    total = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_id,
        )
    ) or 0
    upcoming = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_id,
            Appointment.scheduled_start > now,
            Appointment.status.in_(ACTIVE_STATUSES),
        )
    ) or 0
    completed = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_id,
            Appointment.status == AppointmentStatus.COMPLETED.value,
        )
    ) or 0
    last = db.scalar(
        select(func.max(Appointment.scheduled_start)).where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_id,
        )
    )
    notes = db.scalars(
        select(Appointment.patient_notes)
        .where(
            Appointment.doctor_id == doctor.id,
            Appointment.patient_id == patient_id,
            Appointment.patient_notes.isnot(None),
        )
        .order_by(Appointment.scheduled_start.desc())
        .limit(3)
    ).all()

    name = patient.full_name
    return DoctorPatientDetail(
        id=patient.id,
        name=name,
        initials=_initials(name),
        phone=patient.phone,
        email=patient.email,
        total_visits=total,
        last_visit=ensure_utc(last).isoformat() if last else None,
        upcoming_visits=upcoming,
        completed_visits=completed,
        recent_notes=[n for n in notes if n],
    )


def get_recent_activity(db: Session, user: User, limit: int = 10) -> list[DoctorActivityItem]:
    doctor = _doctor_for_user(db, user)
    rows = db.scalars(
        select(AppointmentStatusHistory)
        .join(Appointment, AppointmentStatusHistory.appointment_id == Appointment.id)
        .options(
            joinedload(AppointmentStatusHistory.appointment).joinedload(Appointment.patient),
        )
        .where(Appointment.doctor_id == doctor.id)
        .order_by(AppointmentStatusHistory.created_at.desc())
        .limit(limit)
    ).unique().all()

    items = []
    for row in rows:
        appt = row.appointment
        patient_name = appt.patient.full_name if appt and appt.patient else "Patient"
        items.append(
            DoctorActivityItem(
                id=row.id,
                appointment_id=row.appointment_id,
                patient_name=patient_name,
                status=row.status,
                status_label=STATUS_LABELS.get(row.status, row.status.title()),
                notes=row.notes,
                created_at=ensure_utc(row.created_at).isoformat(),
            )
        )
    return items


def get_calendar(db: Session, user: User, month: str | None = None) -> list[DoctorCalendarDay]:
    doctor = _doctor_for_user(db, user)
    now = utcnow()

    if month:
        try:
            year, mon = map(int, month.split("-"))
            start = datetime(year, mon, 1, tzinfo=now.tzinfo)
        except ValueError as exc:
            raise NotFoundError("Invalid month format - use YYYY-MM") from exc
    else:
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)

    rows = db.execute(
        select(
            func.date(Appointment.scheduled_start),
            func.count(Appointment.id),
        )
        .where(
            Appointment.doctor_id == doctor.id,
            Appointment.scheduled_start >= start,
            Appointment.scheduled_start < end,
            Appointment.status != AppointmentStatus.CANCELLED.value,
        )
        .group_by(func.date(Appointment.scheduled_start))
    ).all()

    counts = {str(row[0]): row[1] for row in rows}
    days_in_month = (end - start).days
    calendar = []
    for i in range(days_in_month):
        day = (start + timedelta(days=i)).date()
        key = day.isoformat()
        count = counts.get(key, 0)
        calendar.append(
            DoctorCalendarDay(
                date=key,
                count=count,
                label=day.strftime("%d"),
            )
        )
    return calendar


def _update_status(
    db: Session,
    user: User,
    appointment_id: int,
    new_status: str,
    *,
    notes: str,
    cancellation_reason: str | None = None,
) -> DoctorAppointmentItem:
    doctor = _doctor_for_user(db, user)
    appt = db.scalar(
        select(Appointment)
        .options(joinedload(Appointment.patient), joinedload(Appointment.payment))
        .where(Appointment.id == appointment_id, Appointment.doctor_id == doctor.id)
        .with_for_update()
    )
    if not appt:
        raise NotFoundError("Appointment not found")

    if appt.status == AppointmentStatus.CANCELLED.value:
        raise ConflictError("Cancelled appointments cannot be modified")
    if appt.status == AppointmentStatus.COMPLETED.value:
        raise ConflictError("Completed appointments cannot be modified")

    appt.status = new_status
    if cancellation_reason:
        appt.cancellation_reason = cancellation_reason
        appt.cancelled_at = utcnow()

    if new_status == AppointmentStatus.CANCELLED.value:
        release_availability_for_appointment(db, appt)

    db.add(
        AppointmentStatusHistory(
            appointment_id=appt.id,
            status=new_status,
            changed_by_user_id=user.id,
            notes=notes,
        )
    )
    db.commit()
    db.refresh(appt)
    return _serialize_appointment(appt)


def approve_appointment(db: Session, user: User, appointment_id: int) -> DoctorAppointmentItem:
    """Doctor confirms appointment and notifies the patient (web + SMS).

    After payment the booking is often already `confirmed`. In that case we still
    allow this action so the patient receives the doctor-confirm SMS without
    changing status again.
    """
    # get_appointment returns a schema (DoctorAppointmentItem), not an ORM row
    current = get_appointment(db, user, appointment_id)

    if current.status in (
        AppointmentStatus.PENDING.value,
        AppointmentStatus.SCHEDULED.value,
    ):
        result = _update_status(
            db,
            user,
            appointment_id,
            AppointmentStatus.CONFIRMED.value,
            notes="Approved by doctor",
        )
    elif current.status == AppointmentStatus.CONFIRMED.value:
        # Already confirmed (e.g. after payment) - keep status, just notify
        result = current
    else:
        raise ConflictError(
            "Only pending, scheduled, or confirmed appointments can be approved"
        )

    # Notify patient after status is saved - never breaks approve if SMS fails
    try:
        _notify_patient_doctor_confirmed(db, appointment_id)
    except Exception:
        logger.exception(
            "Doctor-confirm notification failed for appointment %s (status already saved)",
            appointment_id,
        )
    return result


def _doctor_confirm_sms_already_sent(db: Session, appointment_id: int) -> bool:
    return (
        db.scalar(
            select(Notification.id).where(
                Notification.appointment_id == appointment_id,
                Notification.notification_type == NotificationType.BOOKING_CONFIRMED.value,
                Notification.channel == NotificationChannel.SMS.value,
            )
        )
        is not None
    )


def _notify_patient_doctor_confirmed(db: Session, appointment_id: int) -> None:
    """Create web + SMS messages after doctor approves. Safe to call more than once."""
    # Pick up .env changes after server restart without stale false negatives
    get_settings.cache_clear()

    appt = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
        )
        .where(Appointment.id == appointment_id)
    )
    if not appt or not appt.patient:
        logger.warning("Doctor-confirm notify skipped - appointment/patient missing (%s)", appointment_id)
        return

    patient = appt.patient
    doctor = appt.doctor
    doctor_name = "your doctor"
    department = "General"
    if doctor:
        name = doctor.user.full_name if doctor.user else f"Doctor #{doctor.id}"
        doctor_name = name if name.startswith("Dr.") else f"Dr. {name}"
        if doctor.specialization:
            department = doctor.specialization.name

    start = ensure_utc(appt.scheduled_start)
    now = utcnow()
    web_message = (
        f"Your appointment with {doctor_name} ({department}) on "
        f"{start.strftime('%A, %d %B %Y')} at {start.strftime('%H:%M')} "
        f"has been confirmed by the doctor."
    )

    # Avoid duplicate web rows if doctor clicks Approve twice
    web_exists = db.scalar(
        select(Notification.id).where(
            Notification.appointment_id == appt.id,
            Notification.notification_type == NotificationType.BOOKING_CONFIRMED.value,
            Notification.channel == NotificationChannel.WEB.value,
            Notification.title == "Appointment confirmed by doctor",
        )
    )
    if not web_exists:
        db.add(
            Notification(
                user_id=patient.id,
                appointment_id=appt.id,
                notification_type=NotificationType.BOOKING_CONFIRMED.value,
                channel=NotificationChannel.WEB.value,
                title="Appointment confirmed by doctor",
                message=web_message,
                is_read=False,
                sent_at=now,
            )
        )

    settings = get_settings()
    if not settings.sms_doctor_confirm_enabled:
        db.commit()
        logger.info("Doctor-confirm SMS disabled via SMS_DOCTOR_CONFIRM_ENABLED")
        return

    if not patient.phone:
        db.commit()
        logger.info("Doctor-confirm SMS skipped - no phone (appointment %s)", appt.id)
        return

    if _doctor_confirm_sms_already_sent(db, appt.id):
        db.commit()
        logger.info("Doctor-confirm SMS already sent for appointment %s", appt.id)
        return

    body = sms_templates.format_doctor_confirm_sms(
        patient,
        doctor_name=doctor_name,
        department=department,
        scheduled_start=appt.scheduled_start,
    )

    try:
        sent = sms_service.send_sms(to_phone=patient.phone, message=body)
    except Exception:
        logger.exception("Doctor-confirm SMS send failed for appointment %s", appt.id)
        sent = False

    db.add(
        Notification(
            user_id=patient.id,
            appointment_id=appt.id,
            notification_type=NotificationType.BOOKING_CONFIRMED.value,
            channel=NotificationChannel.SMS.value,
            title="Appointment confirmed by doctor",
            message=body,
            is_read=False,
            sent_at=now if sent and sms_service.is_sms_configured() else None,
        )
    )
    db.commit()
    if sent and sms_service.is_sms_configured():
        logger.info(
            "Doctor-confirm SMS sent for appointment %s to %s",
            appt.id,
            patient.phone,
        )
    else:
        logger.warning(
            "Doctor-confirm SMS not delivered for appointment %s (sent=%s configured=%s phone=%s)",
            appt.id,
            sent,
            sms_service.is_sms_configured(),
            patient.phone,
        )


def cancel_appointment(
    db: Session,
    user: User,
    appointment_id: int,
    reason: str,
) -> DoctorAppointmentItem:
    appt = get_appointment(db, user, appointment_id)
    if appt.status not in ACTIVE_STATUSES:
        raise ConflictError("This appointment cannot be cancelled")
    return _update_status(
        db, user, appointment_id,
        AppointmentStatus.CANCELLED.value,
        notes="Cancelled by doctor",
        cancellation_reason=reason.strip(),
    )


def complete_appointment(db: Session, user: User, appointment_id: int) -> DoctorAppointmentItem:
    appt = get_appointment(db, user, appointment_id)
    if appt.status not in (
        AppointmentStatus.CONFIRMED.value,
        AppointmentStatus.SCHEDULED.value,
    ):
        raise ConflictError("Only confirmed or scheduled appointments can be completed")
    return _update_status(
        db, user, appointment_id,
        AppointmentStatus.COMPLETED.value,
        notes="Marked complete by doctor",
    )
