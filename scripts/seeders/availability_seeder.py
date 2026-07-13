"""Seed doctor availability slots for the booking engine."""

import re
from datetime import UTC, datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Doctor, DoctorAvailability
from app.models.enums import AvailabilityStatus
from app.utils.helpers import utcnow

SLOT_MINUTES = 30


def _parse_hours(hours_str: str) -> tuple[time, time] | None:
    if not hours_str:
        return time(9, 0), time(17, 0)

    match = re.search(r"(\d{1,2}):(\d{2})\s*[-\-]\s*(\d{1,2}):(\d{2})", hours_str)
    if not match:
        return time(9, 0), time(17, 0)

    return (
        time(int(match.group(1)), int(match.group(2))),
        time(int(match.group(3)), int(match.group(4))),
    )


def _slots_for_day(day_start: time, day_end: time) -> list[tuple[time, time]]:
    slots = []
    current = datetime.combine(datetime.min.date(), day_start)
    end = datetime.combine(datetime.min.date(), day_end)

    while current + timedelta(minutes=SLOT_MINUTES) <= end:
        slot_end = current + timedelta(minutes=SLOT_MINUTES)
        slots.append((current.time(), slot_end.time()))
        current = slot_end

    return slots


def seed_availability(db: Session, days: int = 14) -> int:
    """Create 30-minute slots for verified doctors on their working days."""
    now = utcnow()
    doctors = db.scalars(
        select(Doctor).where(Doctor.is_verified.is_(True), Doctor.is_accepting_patients.is_(True))
    ).all()

    created = 0
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for doctor in doctors:
        working_days = doctor.working_days_list or weekday_names[:5]
        day_start, day_end = _parse_hours(doctor.working_hours or "09:00 - 17:00")
        time_slots = _slots_for_day(day_start, day_end)

        for offset in range(days):
            day = (now + timedelta(days=offset)).date()
            day_name = weekday_names[day.weekday()]
            if day_name not in working_days:
                continue

            for start_t, end_t in time_slots:
                slot_start = datetime.combine(day, start_t, tzinfo=UTC)
                slot_end = datetime.combine(day, end_t, tzinfo=UTC)

                if slot_start <= now:
                    continue

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
                        slot_end=slot_end,
                        status=AvailabilityStatus.AVAILABLE.value,
                    )
                )
                created += 1

    db.commit()
    return created
