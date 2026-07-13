"""Appointment booking - slot queries and duplicate-safe booking."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Appointment,
    AppointmentStatusHistory,
    Doctor,
    DoctorAvailability,
    Payment,
    User,
)
from app.models.enums import AppointmentStatus, AvailabilityStatus, PaymentStatus
from app.schemas.appointment import (
    SLOT_CONFLICT_MESSAGE,
    BookingDoctor,
    BookingSlot,
    BookingSummary,
    CreateBookingRequest,
)
from app.utils.exceptions import ConflictError, NotFoundError
from app.utils.helpers import ensure_utc, utcnow

GRADIENTS = ["primary", "teal", "green", "amber"]

STATUS_LABELS = {
    AppointmentStatus.PENDING.value: "Pending Payment",
    AppointmentStatus.SCHEDULED.value: "Scheduled",
    AppointmentStatus.CONFIRMED.value: "Confirmed",
    AppointmentStatus.COMPLETED.value: "Completed",
    AppointmentStatus.CANCELLED.value: "Cancelled",
    AppointmentStatus.NO_SHOW.value: "No Show",
}


def _display_name(doctor: Doctor) -> str:
    name = doctor.user.full_name if doctor.user else f"Doctor #{doctor.id}"
    if not name.startswith("Dr."):
        return f"Dr. {name}"
    return name


def _doctor_initials(name: str) -> str:
    parts = name.replace("Dr. ", "").split()
    return "".join(p[0] for p in parts[:2]).upper()


def _parse_date(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError as exc:
        raise NotFoundError("Invalid date format") from exc


def _day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=UTC)
    end = datetime.combine(day, time.max, tzinfo=UTC)
    return start, end


def _format_date_label(day: date) -> str:
    return day.strftime("%A, %d %B %Y")


def _slot_is_booked(db: Session, doctor_id: int, slot_start: datetime) -> bool:
    """Verify in SQLite whether doctor + date + time is already booked."""
    existing = db.scalar(
        select(Appointment.id).where(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_start == slot_start,
            Appointment.status != AppointmentStatus.CANCELLED.value,
        )
    )
    return existing is not None


def get_booking_doctor(db: Session, doctor_id: int) -> BookingDoctor | None:
    doctor = db.scalar(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.id == doctor_id, Doctor.is_verified.is_(True))
    )
    if not doctor:
        return None

    name = _display_name(doctor)
    spec = doctor.specialization
    return BookingDoctor(
        id=doctor.id,
        name=name,
        specialization=spec.name if spec else "General",
        department=spec.name if spec else "General Medicine",
        hospital=doctor.hospital_name,
        fee=float(doctor.consultation_fee),
        currency=doctor.currency,
        initials=_doctor_initials(name),
        avatar_gradient=GRADIENTS[doctor.id % len(GRADIENTS)],
        image_url=doctor.avatar_url,
        is_accepting_patients=doctor.is_accepting_patients,
    )


def list_booking_doctors(db: Session) -> list[BookingDoctor]:
    doctors = db.scalars(
        select(Doctor)
        .options(joinedload(Doctor.user), joinedload(Doctor.specialization))
        .where(Doctor.is_verified.is_(True), Doctor.is_accepting_patients.is_(True))
        .order_by(Doctor.rating.desc())
    ).unique().all()

    result = []
    for doctor in doctors:
        name = _display_name(doctor)
        spec = doctor.specialization
        result.append(
            BookingDoctor(
                id=doctor.id,
                name=name,
                specialization=spec.name if spec else "General",
                department=spec.name if spec else "General Medicine",
                hospital=doctor.hospital_name,
                fee=float(doctor.consultation_fee),
                currency=doctor.currency,
                initials=_doctor_initials(name),
                avatar_gradient=GRADIENTS[doctor.id % len(GRADIENTS)],
                image_url=doctor.avatar_url,
                is_accepting_patients=doctor.is_accepting_patients,
            )
        )
    return result


def get_slots_for_date(db: Session, doctor_id: int, date_str: str) -> list[BookingSlot]:
    doctor = db.get(Doctor, doctor_id)
    if not doctor or not doctor.is_verified:
        raise NotFoundError("Doctor not found")

    day = _parse_date(date_str)
    day_start, day_end = _day_bounds(day)
    now = utcnow()

    slots = db.scalars(
        select(DoctorAvailability)
        .where(
            DoctorAvailability.doctor_id == doctor_id,
            DoctorAvailability.slot_start >= day_start,
            DoctorAvailability.slot_start <= day_end,
        )
        .order_by(DoctorAvailability.slot_start.asc())
    ).all()

    result: list[BookingSlot] = []
    for slot in slots:
        start = ensure_utc(slot.slot_start)
        end = ensure_utc(slot.slot_end)

        if start < now and slot.status == AvailabilityStatus.AVAILABLE.value:
            continue

        is_available = (
            slot.status == AvailabilityStatus.AVAILABLE.value
            and not _slot_is_booked(db, doctor_id, start)
        )

        result.append(
            BookingSlot(
                id=slot.id,
                date=day.isoformat(),
                start_time=start.strftime("%H:%M"),
                end_time=end.strftime("%H:%M"),
                status=AvailabilityStatus.BOOKED.value if not is_available else slot.status,
                is_available=is_available,
            )
        )

    return result


def _build_summary(db: Session, appointment: Appointment) -> BookingSummary:
    doctor = appointment.doctor
    name = _display_name(doctor) if doctor else "Unknown"
    spec = doctor.specialization.name if doctor and doctor.specialization else "General"
    start = ensure_utc(appointment.scheduled_start)
    end = ensure_utc(appointment.scheduled_end)

    return BookingSummary(
        appointment_id=appointment.id,
        doctor_name=name,
        department=spec,
        specialization=spec,
        hospital=doctor.hospital_name if doctor else "",
        date=start.date().isoformat(),
        date_label=_format_date_label(start.date()),
        time=start.strftime("%H:%M"),
        time_range=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
        consultation_fee=float(doctor.consultation_fee) if doctor else 0,
        currency=doctor.currency if doctor else "TZS",
        status=appointment.status,
        status_label=STATUS_LABELS.get(appointment.status, appointment.status.title()),
        patient_notes=appointment.patient_notes,
        payment_url=f"/appointments/payment/{appointment.id}",
    )


def create_booking(
    db: Session,
    patient: User,
    payload: CreateBookingRequest,
) -> BookingSummary:
    doctor = db.scalar(
        select(Doctor)
        .options(joinedload(Doctor.specialization))
        .where(Doctor.id == payload.doctor_id, Doctor.is_verified.is_(True))
    )
    if not doctor:
        raise NotFoundError("Doctor not found")
    if not doctor.is_accepting_patients:
        raise ConflictError("This doctor is not accepting new patients")

    slot = db.scalar(
        select(DoctorAvailability)
        .where(
            DoctorAvailability.id == payload.availability_id,
            DoctorAvailability.doctor_id == payload.doctor_id,
        )
        .with_for_update()
    )
    if not slot:
        raise NotFoundError("Time slot not found")

    slot_start = ensure_utc(slot.slot_start)
    slot_end = ensure_utc(slot.slot_end)

    if slot_start < utcnow():
        raise ConflictError("This time slot has passed. Please choose another available time.")

    if slot.status != AvailabilityStatus.AVAILABLE.value or _slot_is_booked(
        db, payload.doctor_id, slot_start
    ):
        raise ConflictError(SLOT_CONFLICT_MESSAGE)

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=payload.doctor_id,
        availability_id=slot.id,
        scheduled_start=slot_start,
        scheduled_end=slot_end,
        status=AppointmentStatus.PENDING.value,
        patient_notes=(payload.patient_notes or "").strip() or None,
    )
    db.add(appointment)
    db.flush()

    slot.status = AvailabilityStatus.BOOKED.value

    db.add(
        AppointmentStatusHistory(
            appointment_id=appointment.id,
            status=AppointmentStatus.PENDING.value,
            changed_by_user_id=patient.id,
            notes="Appointment booked - awaiting payment",
        )
    )

    ref = f"MED-PEND-{appointment.id:06d}"
    db.add(
        Payment(
            appointment_id=appointment.id,
            amount=doctor.consultation_fee,
            currency=doctor.currency,
            status=PaymentStatus.PENDING.value,
            reference_number=ref,
            phone_number=patient.phone,
        )
    )

    db.commit()
    db.refresh(appointment)

    appointment = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
        )
        .where(Appointment.id == appointment.id)
    )
    return _build_summary(db, appointment)


def release_availability_for_appointment(db: Session, appointment: Appointment) -> None:
    """Return a booked slot to the available pool when an appointment is cancelled."""
    if not appointment.availability_id:
        return

    slot = db.scalar(
        select(DoctorAvailability)
        .where(DoctorAvailability.id == appointment.availability_id)
        .with_for_update()
    )
    if slot and slot.status == AvailabilityStatus.BOOKED.value:
        slot.status = AvailabilityStatus.AVAILABLE.value


def get_booking_summary(db: Session, patient_id: int, appointment_id: int) -> BookingSummary | None:
    appointment = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
        )
        .where(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
    )
    if not appointment:
        return None
    return _build_summary(db, appointment)
