"""Doctor directory - database queries and serialization."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models import Doctor, DoctorAvailability, DoctorReview, Specialization
from app.models.enums import AvailabilityStatus
from app.schemas.doctor import (
    AvailabilityDay,
    AvailabilitySlot,
    DoctorDirectoryMeta,
    DoctorListItem,
    DoctorProfile,
    DoctorReviewItem,
    SpecializationOption,
)
from app.utils.helpers import ensure_utc, utcnow

GRADIENTS = ["primary", "teal", "green", "amber"]

FEE_RANGES = [
    {"id": "any", "label": "Any fee", "min": 0, "max": 999999999},
    {"id": "under-50k", "label": "Under 50,000 TZS", "min": 0, "max": 50000},
    {"id": "50k-80k", "label": "50,000 - 80,000 TZS", "min": 50000, "max": 80000},
    {"id": "80k-100k", "label": "80,000 - 100,000 TZS", "min": 80000, "max": 100000},
    {"id": "100k-plus", "label": "100,000+ TZS", "min": 100000, "max": 999999999},
]


def _initials(name: str) -> str:
    parts = name.replace("Dr. ", "").split()
    return "".join(p[0] for p in parts[:2]).upper()


def _slots_today(db: Session, doctor_id: int, now) -> int:
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return db.scalar(
        select(func.count(DoctorAvailability.id)).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.status == AvailabilityStatus.AVAILABLE.value,
            DoctorAvailability.slot_start >= now,
            DoctorAvailability.slot_start <= today_end,
        )
    ) or 0


def _week_slots(db: Session, doctor_id: int, now) -> int:
    week_end = now + timedelta(days=7)
    return db.scalar(
        select(func.count(DoctorAvailability.id)).where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.status == AvailabilityStatus.AVAILABLE.value,
            DoctorAvailability.slot_start >= now,
            DoctorAvailability.slot_start <= week_end,
        )
    ) or 0


def _display_name(doctor: Doctor) -> str:
    name = doctor.user.full_name if doctor.user else f"Doctor #{doctor.id}"
    if not name.startswith("Dr."):
        return f"Dr. {name}"
    return name


def _serialize_doctor(db: Session, doctor: Doctor, now) -> DoctorListItem:
    name = _display_name(doctor)
    spec = doctor.specialization
    slots = _slots_today(db, doctor.id, now)
    available_today = slots > 0

    if available_today:
        availability_label = f"Available today · {slots} slots"
    elif _week_slots(db, doctor.id, now) > 0:
        availability_label = "Available this week"
    elif doctor.is_accepting_patients:
        availability_label = "Booking open"
    else:
        availability_label = "Not accepting patients"

    return DoctorListItem(
        id=doctor.id,
        name=name,
        initials=_initials(name),
        specialization=spec.name if spec else "General",
        specialization_slug=spec.slug if spec else "",
        qualification=doctor.qualification or "MBBS",
        hospital=doctor.hospital_name,
        image_url=doctor.avatar_url,
        avatar_gradient=GRADIENTS[doctor.id % len(GRADIENTS)],
        rating=float(doctor.rating or 4.8),
        review_count=doctor.review_count or 0,
        experience_years=doctor.experience_years,
        fee=float(doctor.consultation_fee),
        currency=doctor.currency,
        gender=doctor.gender or "",
        available_today=available_today,
        availability_label=availability_label,
        slots_today=slots,
        short_bio=doctor.short_bio or (doctor.bio[:200] + "…" if doctor.bio and len(doctor.bio) > 200 else doctor.bio or ""),
        profile_url=f"/doctors/{doctor.id}",
        book_url=f"/appointments/book?doctor={doctor.id}",
    )


def _filtered_query(
    q: str | None = None,
    specialization: str | None = None,
    gender: str | None = None,
    fee_min: float | None = None,
    fee_max: float | None = None,
):
    from app.models import User

    stmt = (
        select(Doctor)
        .join(User, Doctor.user_id == User.id)
        .join(Specialization, Doctor.specialization_id == Specialization.id)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.is_verified.is_(True))
    )

    if q:
        term = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                Specialization.name.ilike(term),
                Doctor.hospital_name.ilike(term),
                Doctor.qualification.ilike(term),
            )
        )

    if specialization:
        slug = specialization.strip().lower().replace(" ", "-")
        stmt = stmt.where(
            or_(
                Specialization.slug == slug,
                Specialization.name.ilike(specialization.strip()),
            )
        )

    if gender:
        stmt = stmt.where(Doctor.gender == gender.lower())

    if fee_min is not None:
        stmt = stmt.where(Doctor.consultation_fee >= fee_min)
    if fee_max is not None:
        stmt = stmt.where(Doctor.consultation_fee <= fee_max)

    return stmt.order_by(Doctor.rating.desc(), Doctor.experience_years.desc())


def list_doctors(
    db: Session,
    *,
    q: str | None = None,
    specialization: str | None = None,
    availability: str | None = None,
    gender: str | None = None,
    fee_min: float | None = None,
    fee_max: float | None = None,
) -> list[DoctorListItem]:
    now = utcnow()
    stmt = _filtered_query(q, specialization, gender, fee_min, fee_max)
    doctors = db.scalars(stmt).unique().all()
    items = [_serialize_doctor(db, d, now) for d in doctors]

    if availability == "today":
        items = [d for d in items if d.available_today]
    elif availability == "week":
        items = [d for d in items if d.available_today or "week" in d.availability_label.lower()]

    return items


def get_directory_meta(db: Session) -> DoctorDirectoryMeta:
    specs = db.execute(
        select(
            Specialization.id,
            Specialization.name,
            Specialization.slug,
            Specialization.icon,
            func.count(Doctor.id),
        )
        .outerjoin(Doctor, (Doctor.specialization_id == Specialization.id) & Doctor.is_verified.is_(True))
        .where(Specialization.is_active.is_(True))
        .group_by(Specialization.id)
        .order_by(Specialization.name)
    ).all()

    total = db.scalar(
        select(func.count(Doctor.id)).where(Doctor.is_verified.is_(True))
    ) or 0

    return DoctorDirectoryMeta(
        total=total,
        specializations=[
            SpecializationOption(
                id=row[0],
                name=row[1],
                slug=row[2],
                icon=row[3],
                doctor_count=row[4] or 0,
            )
            for row in specs
        ],
        fee_ranges=FEE_RANGES,
    )


def _build_calendar(db: Session, doctor_id: int, days: int = 14) -> list[AvailabilityDay]:
    now = utcnow()
    end = now + timedelta(days=days)

    slots = db.scalars(
        select(DoctorAvailability)
        .where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.slot_start >= now,
            DoctorAvailability.slot_start <= end,
            DoctorAvailability.status == AvailabilityStatus.AVAILABLE.value,
        )
        .order_by(DoctorAvailability.slot_start.asc())
    ).all()

    by_date: dict[str, list[AvailabilitySlot]] = {}
    for slot in slots:
        start = ensure_utc(slot.slot_start)
        end_t = ensure_utc(slot.slot_end)
        date_key = start.date().isoformat()
        by_date.setdefault(date_key, []).append(
            AvailabilitySlot(
                id=slot.id,
                date=date_key,
                start_time=start.strftime("%H:%M"),
                end_time=end_t.strftime("%H:%M"),
                status=slot.status,
            )
        )

    calendar = []
    for i in range(days):
        day = (now + timedelta(days=i)).date()
        date_key = day.isoformat()
        calendar.append(
            AvailabilityDay(
                date=date_key,
                label=day.strftime("%a, %d %b"),
                slots=by_date.get(date_key, []),
            )
        )
    return calendar


def get_doctor_profile(db: Session, doctor_id: int) -> DoctorProfile | None:
    now = utcnow()
    doctor = db.scalar(
        select(Doctor)
        .options(
            joinedload(Doctor.user),
            joinedload(Doctor.specialization),
            joinedload(Doctor.reviews),
        )
        .where(Doctor.id == doctor_id, Doctor.is_verified.is_(True))
    )

    if not doctor:
        return None

    base = _serialize_doctor(db, doctor, now)
    reviews = sorted(doctor.reviews, key=lambda r: r.created_at, reverse=True)

    return DoctorProfile(
        **base.model_dump(),
        bio=doctor.bio or base.short_bio,
        education=doctor.education_list,
        working_days=doctor.working_days_list,
        working_hours=doctor.working_hours or "09:00 - 17:00",
        languages=doctor.languages_list,
        is_accepting_patients=doctor.is_accepting_patients,
        is_verified=doctor.is_verified,
        reviews=[
            DoctorReviewItem(
                id=r.id,
                patient_name=r.patient_name,
                rating=r.rating,
                comment=r.comment,
                created_at=ensure_utc(r.created_at).isoformat(),
            )
            for r in reviews
        ],
        availability_calendar=_build_calendar(db, doctor.id),
    )
