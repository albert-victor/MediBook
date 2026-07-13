"""Seed appointments, payments, notifications, and availability for dashboard demo."""

import secrets
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Appointment,
    AppointmentStatusHistory,
    Doctor,
    DoctorAvailability,
    Notification,
    Payment,
    User,
)
from app.models.enums import (
    AppointmentStatus,
    AvailabilityStatus,
    NotificationChannel,
    NotificationType,
    PaymentMethod,
    PaymentStatus,
)
from app.utils.helpers import utcnow

DEMO_PATIENT_EMAIL = "amina.hassan@email.com"


def seed_dashboard_data(db: Session) -> dict[str, int]:
    patient = db.scalar(select(User).where(User.email == DEMO_PATIENT_EMAIL))
    if not patient:
        return {"appointments": 0, "payments": 0, "notifications": 0, "slots": 0}

    doctors = db.scalars(select(Doctor).limit(6)).all()
    if not doctors:
        return {"appointments": 0, "payments": 0, "notifications": 0, "slots": 0}

    now = utcnow()
    counts = {"appointments": 0, "payments": 0, "notifications": 0, "slots": 0}

    # Availability slots for today and tomorrow
    for doctor in doctors[:4]:
        for hour in (9, 11, 14, 16):
            slot_start = now.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=1)
            if slot_start <= now:
                slot_start += timedelta(days=1)
            exists = db.scalar(
                select(DoctorAvailability.id).where(
                    DoctorAvailability.doctor_id == doctor.id,
                    DoctorAvailability.slot_start == slot_start,
                )
            )
            if exists:
                continue
            db.add(
                DoctorAvailability(
                    doctor_id=doctor.id,
                    slot_start=slot_start,
                    slot_end=slot_start + timedelta(minutes=30),
                    status=AvailabilityStatus.AVAILABLE.value,
                )
            )
            counts["slots"] += 1

    # Skip if patient already has appointments
    existing = db.scalar(
        select(Appointment.id).where(Appointment.patient_id == patient.id).limit(1)
    )
    if existing:
        db.commit()
        return counts

    scenarios = [
        # upcoming confirmed
        (doctors[0], now + timedelta(days=2, hours=3), AppointmentStatus.CONFIRMED, PaymentStatus.COMPLETED, True),
        # upcoming scheduled
        (doctors[1], now + timedelta(days=5), AppointmentStatus.SCHEDULED, PaymentStatus.PENDING, True),
        # past completed
        (doctors[0], now - timedelta(days=14), AppointmentStatus.COMPLETED, PaymentStatus.COMPLETED, True),
        (doctors[2], now - timedelta(days=30), AppointmentStatus.COMPLETED, PaymentStatus.COMPLETED, True),
        (doctors[3], now - timedelta(days=45), AppointmentStatus.COMPLETED, PaymentStatus.COMPLETED, True),
        # cancelled
        (doctors[1], now - timedelta(days=7), AppointmentStatus.CANCELLED, None, False),
    ]

    for doctor, start, status, pay_status, with_payment in scenarios:
        end = start + timedelta(minutes=30)
        appt = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            scheduled_start=start,
            scheduled_end=end,
            status=status.value,
        )
        db.add(appt)
        db.flush()

        db.add(
            AppointmentStatusHistory(
                appointment_id=appt.id,
                status=status.value,
                changed_by_user_id=patient.id,
                notes="Initial status",
            )
        )
        counts["appointments"] += 1

        if with_payment and pay_status:
            ref = f"MED-{secrets.token_hex(4).upper()}"
            db.add(
                Payment(
                    appointment_id=appt.id,
                    amount=doctor.consultation_fee,
                    currency=doctor.currency,
                    payment_method=PaymentMethod.MPESA.value,
                    status=pay_status.value,
                    reference_number=ref,
                    phone_number=patient.phone,
                    paid_at=start if pay_status == PaymentStatus.COMPLETED else None,
                )
            )
            counts["payments"] += 1

    notifications_data = [
        (NotificationType.APPOINTMENT_REMINDER, "Upcoming appointment", "Your visit is in 2 days. Don't forget to arrive early."),
        (NotificationType.BOOKING_CONFIRMED, "Booking confirmed", "Your appointment has been confirmed successfully."),
        (NotificationType.PAYMENT_SUCCESS, "Payment received", "We received your M-Pesa payment. Reference saved."),
        (NotificationType.GENERAL, "Welcome to mediBook", "Your health dashboard is ready. Book your next visit anytime."),
    ]
    upcoming = db.scalar(
        select(Appointment)
        .where(Appointment.patient_id == patient.id, Appointment.scheduled_start > now)
        .order_by(Appointment.scheduled_start.asc())
        .limit(1)
    )
    for ntype, title, message in notifications_data:
        db.add(
            Notification(
                user_id=patient.id,
                appointment_id=upcoming.id if upcoming and ntype == NotificationType.APPOINTMENT_REMINDER else None,
                notification_type=ntype.value,
                channel=NotificationChannel.WEB.value,
                title=title,
                message=message,
                is_read=ntype == NotificationType.GENERAL,
                sent_at=now,
            )
        )
        counts["notifications"] += 1

    db.commit()
    return counts
