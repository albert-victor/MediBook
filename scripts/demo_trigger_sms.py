"""Book a near-term demo appointment and fire reminder SMS immediately.

Usage:
  python scripts/demo_trigger_sms.py --phone 0748952582
  python scripts/demo_trigger_sms.py --email amina.hassan@email.com --phone 0748952582
"""

from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import Appointment, Doctor, DoctorAvailability, Notification, User
from app.models.enums import (
    AppointmentStatus,
    AvailabilityStatus,
    NotificationChannel,
    NotificationType,
)
from app.services.reminder_service import process_reminder_check
from app.utils.helpers import utcnow


def main() -> int:
    parser = argparse.ArgumentParser(description="Demo: instant appointment SMS reminder")
    parser.add_argument("--email", default="amina.hassan@email.com")
    parser.add_argument("--phone", default=None, help="Override patient phone for this demo")
    parser.add_argument(
        "--hours",
        type=float,
        default=1.5,
        help="Hours from now for appointment (use <= 2 for 2h SMS window)",
    )
    parser.add_argument("--doctor-id", type=int, default=1)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        patient = db.scalar(select(User).where(User.email == args.email))
        if not patient:
            print(f"Patient not found: {args.email}")
            return 1

        if args.phone:
            patient.phone = args.phone
            print(f"Updated phone for {patient.email} → {patient.phone}")

        if not patient.phone:
            print("Patient has no phone. Pass --phone 07XXXXXXXX")
            return 1

        target = utcnow() + timedelta(hours=args.hours)
        minute = 0 if target.minute < 15 else (30 if target.minute < 45 else 0)
        if target.minute >= 45:
            target = target.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            target = target.replace(minute=minute, second=0, microsecond=0)

        doctor_id = args.doctor_id
        slot = db.scalar(
            select(DoctorAvailability)
            .where(
                DoctorAvailability.doctor_id == doctor_id,
                DoctorAvailability.slot_start >= utcnow() + timedelta(minutes=20),
                DoctorAvailability.slot_start <= utcnow() + timedelta(hours=3),
                DoctorAvailability.status == AvailabilityStatus.AVAILABLE.value,
            )
            .order_by(DoctorAvailability.slot_start.asc())
        )

        if not slot:
            end = target + timedelta(minutes=30)
            existing = db.scalar(
                select(DoctorAvailability).where(
                    DoctorAvailability.doctor_id == doctor_id,
                    DoctorAvailability.slot_start == target,
                )
            )
            if existing:
                slot = existing
                slot.status = AvailabilityStatus.AVAILABLE.value
                slot.slot_end = end
            else:
                slot = DoctorAvailability(
                    doctor_id=doctor_id,
                    slot_start=target,
                    slot_end=end,
                    status=AvailabilityStatus.AVAILABLE.value,
                )
                db.add(slot)
                db.flush()
            print(f"Prepared demo slot at {slot.slot_start.isoformat()}")

        # Drop SMS reminder history for this patient's upcoming bookings with this doctor
        upcoming = list(
            db.scalars(
                select(Appointment.id).where(
                    Appointment.patient_id == patient.id,
                    Appointment.doctor_id == doctor_id,
                    Appointment.scheduled_start > utcnow(),
                )
            )
        )
        if upcoming:
            db.execute(
                delete(Notification).where(
                    Notification.appointment_id.in_(upcoming),
                    Notification.notification_type
                    == NotificationType.APPOINTMENT_REMINDER.value,
                )
            )

        # Avoid unique conflict on doctor_id + scheduled_start
        conflict = db.scalar(
            select(Appointment).where(
                Appointment.doctor_id == doctor_id,
                Appointment.scheduled_start == slot.slot_start,
            )
        )
        if conflict:
            conflict.patient_id = patient.id
            conflict.availability_id = slot.id
            conflict.scheduled_end = slot.slot_end
            conflict.status = AppointmentStatus.CONFIRMED.value
            conflict.patient_notes = "Demo SMS reminder"
            conflict.cancellation_reason = None
            conflict.cancelled_at = None
            appt = conflict
        else:
            appt = Appointment(
                patient_id=patient.id,
                doctor_id=doctor_id,
                availability_id=slot.id,
                scheduled_start=slot.slot_start,
                scheduled_end=slot.slot_end,
                status=AppointmentStatus.CONFIRMED.value,
                patient_notes="Demo SMS reminder",
            )
            db.add(appt)

        slot.status = AvailabilityStatus.BOOKED.value
        db.commit()
        db.refresh(appt)

        doc = db.scalar(
            select(Doctor)
            .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
            .where(Doctor.id == doctor_id)
        )
        doc_name = doc.user.full_name if doc and doc.user else str(doctor_id)
        spec = doc.specialization.name if doc and doc.specialization else ""

        print("--- Demo appointment created ---")
        print(f"Appointment id: {appt.id}")
        print(f"Patient: {patient.full_name} <{patient.email}> phone={patient.phone}")
        print(f"Doctor: Dr. {doc_name} ({spec})")
        print(f"When UTC: {appt.scheduled_start}")
        print(f"Language: {getattr(patient, 'preferred_language', 'sw')}")
        print("Running reminder engine now...")

        result = process_reminder_check(db)
        print(
            f"Reminder result: checked={result.checked} web={result.sent_web} "
            f"email={result.sent_email} sms={result.sent_sms} errors={result.errors}"
        )
        print("\nCheck:")
        print("  1) Your phone for the mediBook SMS")
        print("  2) Patient panel → Notifications (badge: SMS)")
        print(f"  Login: {args.email} / Patient@123456")
        return 0 if result.sent_sms else 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
