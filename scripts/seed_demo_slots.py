"""Seed demo availability for Jul 14 evening + Jul 15 (selected doctors).

Run from project root:
  python scripts/seed_demo_slots.py
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import SessionLocal
from app.models import Doctor, DoctorAvailability
from app.models.enums import AvailabilityStatus
from app.utils.helpers import utcnow

# Diverse specialties for the demo panel
DEMO_DOCTOR_IDS = (1, 2, 3, 5, 7, 8)

# Times stored as UTC and shown as-is in the booking UI
JUL14_TIMES = ("21:00", "21:30", "22:00", "22:30", "23:00")
JUL15_TIMES = (
    "08:00",
    "08:30",
    "09:00",
    "09:30",
    "10:00",
    "10:30",
    "11:00",
    "14:00",
    "14:30",
    "15:00",
    "15:30",
    "16:00",
)


def _parse_hm(value: str) -> tuple[int, int]:
    h, m = value.split(":")
    return int(h), int(m)


def _ensure_slot(db, doctor_id: int, start: datetime) -> bool:
    end = start + timedelta(minutes=30)
    exists = db.scalar(
        select(DoctorAvailability.id).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.slot_start == start,
        )
    )
    if exists:
        # Re-open if it was leftover booked/blocked for demo
        row = db.get(DoctorAvailability, exists)
        if row and row.status != AvailabilityStatus.AVAILABLE.value:
            # Only reopen if no active appointment still points at it
            from app.models import Appointment
            from app.models.enums import AppointmentStatus

            linked = db.scalar(
                select(Appointment.id).where(
                    Appointment.availability_id == row.id,
                    Appointment.status.in_(
                        [
                            AppointmentStatus.PENDING.value,
                            AppointmentStatus.SCHEDULED.value,
                            AppointmentStatus.CONFIRMED.value,
                        ]
                    ),
                )
            )
            if not linked:
                row.status = AvailabilityStatus.AVAILABLE.value
                return True
        return False

    if start <= utcnow():
        return False

    db.add(
        DoctorAvailability(
            doctor_id=doctor_id,
            slot_start=start,
            slot_end=end,
            status=AvailabilityStatus.AVAILABLE.value,
        )
    )
    return True


def main() -> None:
    db = SessionLocal()
    try:
        doctors = (
            db.scalars(
                select(Doctor)
                .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
                .where(Doctor.id.in_(DEMO_DOCTOR_IDS))
                .order_by(Doctor.id)
            )
            .unique()
            .all()
        )
        if not doctors:
            print("No demo doctors found. Run python scripts/seed.py first.")
            return

        created = 0
        print(f"Now UTC: {utcnow().isoformat()}")
        print("--- Doctors receiving demo slots ---")
        for doctor in doctors:
            name = doctor.user.full_name if doctor.user else f"#{doctor.id}"
            spec = doctor.specialization.name if doctor.specialization else "General"
            print(f"  id={doctor.id}  Dr. {name}  ({spec})")

            for hm in JUL14_TIMES:
                h, m = _parse_hm(hm)
                start = datetime(2026, 7, 14, h, m, tzinfo=UTC)
                if _ensure_slot(db, doctor.id, start):
                    created += 1

            for hm in JUL15_TIMES:
                h, m = _parse_hm(hm)
                start = datetime(2026, 7, 15, h, m, tzinfo=UTC)
                if _ensure_slot(db, doctor.id, start):
                    created += 1

        db.commit()
        print(f"\nCreated/reopened slots: {created}")
        print("Jul 14 times (UTC, shown in UI):", ", ".join(JUL14_TIMES))
        print("Jul 15 times (UTC, shown in UI):", ", ".join(JUL15_TIMES))
        print("\nOpen booking -> pick one of the doctors above -> date 14 or 15.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
