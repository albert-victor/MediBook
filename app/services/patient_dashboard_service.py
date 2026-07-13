"""Patient dashboard data aggregation."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Appointment, Doctor, Notification, Payment, User
from app.models.enums import AppointmentStatus, NotificationChannel, PaymentStatus
from app.schemas.patient_dashboard import (
    AppointmentItem,
    DashboardOverview,
    DashboardStats,
    DoctorBrief,
    NotificationItem,
    PaymentItem,
    QuickAction,
    UpcomingAppointment,
    UpcomingReminder,
)
from app.utils.helpers import ensure_utc, utcnow

PAYMENT_METHOD_LABELS = {
    "mpesa": "M-Pesa",
    "mixx": "Mixx by Yas",
    "airtel_money": "Airtel Money",
    "halopesa": "HaloPesa",
    "azampesa": "AzamPesa",
    "selcom_pay": "Selcom Pay",
}

STATUS_LABELS = {
    AppointmentStatus.PENDING.value: "Pending",
    AppointmentStatus.SCHEDULED.value: "Scheduled",
    AppointmentStatus.CONFIRMED.value: "Confirmed",
    AppointmentStatus.COMPLETED.value: "Completed",
    AppointmentStatus.CANCELLED.value: "Cancelled",
    AppointmentStatus.NO_SHOW.value: "No Show",
}

PAYMENT_STATUS_LABELS = {
    PaymentStatus.PENDING.value: "Pending",
    PaymentStatus.PROCESSING.value: "Processing",
    PaymentStatus.COMPLETED.value: "Paid",
    PaymentStatus.FAILED.value: "Failed",
    PaymentStatus.REFUNDED.value: "Refunded",
}

GRADIENTS = ["primary", "teal", "green", "amber"]


def _greeting() -> str:
    hour = utcnow().hour
    if hour < 12:
        return "Good morning"
    if hour < 17:
        return "Good afternoon"
    return "Good evening"


def _doctor_initials(name: str) -> str:
    parts = name.replace("Dr. ", "").split()
    return "".join(p[0] for p in parts[:2]).upper()


def _doctor_brief(doctor: Doctor, available_today: bool = False) -> DoctorBrief:
    name = doctor.user.full_name if doctor.user else f"Dr. #{doctor.id}"
    return DoctorBrief(
        id=doctor.id,
        name=name,
        specialization=doctor.specialization.name if doctor.specialization else "General",
        hospital=doctor.hospital_name,
        fee=float(doctor.consultation_fee),
        currency=doctor.currency,
        rating=4.8,
        initials=_doctor_initials(name),
        avatar_gradient=GRADIENTS[doctor.id % len(GRADIENTS)],
        available_today=available_today,
        profile_url=f"/doctors/{doctor.id}",
        book_url=f"/appointments/book?doctor={doctor.id}",
    )


def _appointment_item(appt: Appointment) -> AppointmentItem:
    doctor = appt.doctor
    name = doctor.user.full_name if doctor and doctor.user else "Unknown"
    spec = doctor.specialization.name if doctor and doctor.specialization else ""
    payment_status = appt.payment.status if appt.payment else None
    payment_url = None
    if appt.status in (AppointmentStatus.PENDING.value, AppointmentStatus.SCHEDULED.value):
        if not payment_status or payment_status == PaymentStatus.PENDING.value:
            payment_url = f"/appointments/payment/{appt.id}"
    return AppointmentItem(
        id=appt.id,
        doctor_name=name,
        specialization=spec,
        hospital=doctor.hospital_name if doctor else "",
        scheduled_start=ensure_utc(appt.scheduled_start).isoformat(),
        scheduled_end=ensure_utc(appt.scheduled_end).isoformat(),
        status=appt.status,
        status_label=STATUS_LABELS.get(appt.status, appt.status.title()),
        payment_status=payment_status,
        payment_url=payment_url,
    )


def get_overview(db: Session, patient: User) -> DashboardOverview:
    now = utcnow()
    stats = get_statistics(db, patient.id)

    upcoming_appt = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
        )
        .where(
            Appointment.patient_id == patient.id,
            Appointment.scheduled_start > now,
            Appointment.status.in_([
                AppointmentStatus.PENDING.value,
                AppointmentStatus.SCHEDULED.value,
                AppointmentStatus.CONFIRMED.value,
            ]),
        )
        .order_by(Appointment.scheduled_start.asc())
        .limit(1)
    )

    upcoming = None
    reminder = None
    if upcoming_appt:
        start = ensure_utc(upcoming_appt.scheduled_start)
        delta = start - now
        upcoming = UpcomingAppointment(
            id=upcoming_appt.id,
            doctor_name=upcoming_appt.doctor.user.full_name,
            specialization=upcoming_appt.doctor.specialization.name,
            hospital=upcoming_appt.doctor.hospital_name,
            scheduled_start=start.isoformat(),
            scheduled_end=ensure_utc(upcoming_appt.scheduled_end).isoformat(),
            status=upcoming_appt.status,
            status_label=STATUS_LABELS.get(upcoming_appt.status, upcoming_appt.status),
            days_until=max(0, delta.days),
            hours_until=max(0, int(delta.total_seconds() // 3600)),
        )
        reminder = UpcomingReminder(
            appointment_id=upcoming_appt.id,
            title="Appointment reminder",
            message=(
                f"Your visit with {upcoming_appt.doctor.user.full_name} "
                f"is in {delta.days} day(s). Please arrive 10 minutes early."
            ),
            scheduled_start=start.isoformat(),
            channel=NotificationChannel.EMAIL.value,
        )

    quick_actions = [
        QuickAction(label="Book Appointment", icon="bi-calendar2-plus", url="/appointments/book", color="primary"),
        QuickAction(label="Find Doctor", icon="bi-search", url="/#search-doctors", color="teal"),
        QuickAction(label="Payment History", icon="bi-credit-card", url="#payments-section", color="green"),
        QuickAction(label="Get Help", icon="bi-headset", url="/help", color="amber"),
    ]

    return DashboardOverview(
        greeting=_greeting(),
        patient_name=patient.first_name,
        stats=stats,
        upcoming=upcoming,
        reminder=reminder,
        quick_actions=quick_actions,
    )


def get_statistics(db: Session, patient_id: int) -> DashboardStats:
    now = utcnow()
    total = db.scalar(
        select(func.count(Appointment.id)).where(Appointment.patient_id == patient_id)
    ) or 0
    completed = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.patient_id == patient_id,
            Appointment.status == AppointmentStatus.COMPLETED.value,
        )
    ) or 0
    upcoming = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.patient_id == patient_id,
            Appointment.scheduled_start > now,
            Appointment.status.in_([
                AppointmentStatus.PENDING.value,
                AppointmentStatus.SCHEDULED.value,
                AppointmentStatus.CONFIRMED.value,
            ]),
        )
    ) or 0
    total_spent: Decimal = db.scalar(
        select(func.coalesce(func.sum(Payment.amount), 0))
        .join(Appointment, Payment.appointment_id == Appointment.id)
        .where(
            Appointment.patient_id == patient_id,
            Payment.status == PaymentStatus.COMPLETED.value,
        )
    ) or Decimal("0")
    unread = db.scalar(
        select(func.count(Notification.id)).where(
            Notification.user_id == patient_id,
            Notification.is_read.is_(False),
        )
    ) or 0

    return DashboardStats(
        total_appointments=total,
        completed=completed,
        upcoming=upcoming,
        total_spent=float(total_spent),
        currency="TZS",
        unread_notifications=unread,
    )


def get_appointment_history(db: Session, patient_id: int, limit: int = 10) -> list[AppointmentItem]:
    appts = db.scalars(
        select(Appointment)
        .options(
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
            joinedload(Appointment.payment),
        )
        .where(Appointment.patient_id == patient_id)
        .order_by(Appointment.scheduled_start.desc())
        .limit(limit)
    ).all()
    return [_appointment_item(a) for a in appts]


def get_payment_history(db: Session, patient_id: int, limit: int = 10) -> list[PaymentItem]:
    payments = db.scalars(
        select(Payment)
        .join(Appointment, Payment.appointment_id == Appointment.id)
        .options(
            joinedload(Payment.appointment)
            .joinedload(Appointment.doctor)
            .joinedload(Doctor.user),
        )
        .where(Appointment.patient_id == patient_id)
        .order_by(Payment.created_at.desc())
        .limit(limit)
    ).all()

    items = []
    for p in payments:
        doctor_name = "-"
        if p.appointment and p.appointment.doctor and p.appointment.doctor.user:
            doctor_name = p.appointment.doctor.user.full_name
        items.append(
            PaymentItem(
                id=p.id,
                appointment_id=p.appointment_id,
                doctor_name=doctor_name,
                amount=float(p.amount),
                currency=p.currency,
                method=p.payment_method,
                method_label=PAYMENT_METHOD_LABELS.get(p.payment_method, p.payment_method),
                status=p.status,
                status_label=PAYMENT_STATUS_LABELS.get(p.status, p.status),
                reference_number=p.reference_number,
                paid_at=ensure_utc(p.paid_at).isoformat() if p.paid_at else None,
            )
        )
    return items


def get_notifications(db: Session, patient_id: int, limit: int = 10) -> list[NotificationItem]:
    from app.services.notification_service import serialize_notification_with_appointment

    notes = db.scalars(
        select(Notification)
        .where(Notification.user_id == patient_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    ).all()
    return [NotificationItem(**serialize_notification_with_appointment(db, n)) for n in notes]


def get_available_doctors(db: Session, limit: int = 6) -> list[DoctorBrief]:
    from app.models import DoctorAvailability
    from app.models.enums import AvailabilityStatus

    now = utcnow()
    today_end = now.replace(hour=23, minute=59, second=59)

    doctors = db.scalars(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.is_verified.is_(True), Doctor.is_accepting_patients.is_(True))
        .order_by(Doctor.id.asc())
        .limit(limit)
    ).all()

    result = []
    for doc in doctors:
        slot_count = db.scalar(
            select(func.count(DoctorAvailability.id)).where(
                DoctorAvailability.doctor_id == doc.id,
                DoctorAvailability.status == AvailabilityStatus.AVAILABLE.value,
                DoctorAvailability.slot_start >= now,
                DoctorAvailability.slot_start <= today_end,
            )
        ) or 0
        result.append(_doctor_brief(doc, available_today=slot_count > 0))
    return result


def get_recently_visited_doctors(db: Session, patient_id: int, limit: int = 4) -> list[DoctorBrief]:
    doctor_ids = db.scalars(
        select(Appointment.doctor_id)
        .where(
            Appointment.patient_id == patient_id,
            Appointment.status.in_([
                AppointmentStatus.COMPLETED.value,
                AppointmentStatus.CONFIRMED.value,
            ]),
        )
        .order_by(Appointment.scheduled_start.desc())
        .distinct()
        .limit(limit)
    ).all()

    if not doctor_ids:
        return []

    doctors = db.scalars(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.id.in_(doctor_ids))
    ).all()
    order = {did: i for i, did in enumerate(doctor_ids)}
    doctors.sort(key=lambda d: order.get(d.id, 99))
    return [_doctor_brief(d) for d in doctors]


def mark_notification_read(db: Session, patient_id: int, notification_id: int) -> bool:
    note = db.get(Notification, notification_id)
    if not note or note.user_id != patient_id:
        return False
    note.is_read = True
    note.read_at = utcnow()
    db.commit()
    return True
