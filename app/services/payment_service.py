"""Simulated payment processing for appointments."""

from __future__ import annotations

import secrets
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Appointment,
    AppointmentStatusHistory,
    Doctor,
    Notification,
    Payment,
)
from app.models.enums import (
    AppointmentStatus,
    NotificationChannel,
    NotificationType,
    PaymentMethod,
    PaymentStatus,
)
from app.schemas.appointment import (
    ConfirmationContext,
    InitiatePaymentResult,
    PaymentContext,
    PaymentMethodOption,
    PaymentResult,
    ProcessPaymentRequest,
)
from app.services.appointment_service import STATUS_LABELS
from app.utils.exceptions import ConflictError, NotFoundError
from app.utils.helpers import ensure_utc, utcnow

SIMULATION_SECONDS = 6

METHOD_LABELS = {
    PaymentMethod.MPESA.value: "M-Pesa",
    PaymentMethod.MIXX.value: "Mixx by Yas",
    PaymentMethod.AIRTEL_MONEY.value: "Airtel Money",
    PaymentMethod.HALOPESA.value: "HaloPesa",
    PaymentMethod.AZAMPESA.value: "AzamPesa",
    PaymentMethod.SELCOM_PAY.value: "Selcom Pay",
}

PAYMENT_STATUS_LABELS = {
    PaymentStatus.PENDING.value: "Pending",
    PaymentStatus.PROCESSING.value: "Processing",
    PaymentStatus.COMPLETED.value: "Paid",
    PaymentStatus.FAILED.value: "Failed",
    PaymentStatus.REFUNDED.value: "Refunded",
}

PAYMENT_METHODS = [
    PaymentMethodOption(id="mpesa", label="M-Pesa", icon="bi-phone"),
    PaymentMethodOption(id="mixx", label="Mixx by Yas", icon="bi-wallet2"),
    PaymentMethodOption(id="airtel_money", label="Airtel Money", icon="bi-phone-fill"),
    PaymentMethodOption(id="halopesa", label="HaloPesa", icon="bi-credit-card"),
    PaymentMethodOption(id="azampesa", label="AzamPesa", icon="bi-bank"),
    PaymentMethodOption(id="selcom_pay", label="Selcom Pay", icon="bi-shield-check"),
]

# Realistic reference prefixes per Tanzanian mobile-money provider
_REF_GENERATORS: dict[str, Callable[[], str]] = {}


def _register_generators() -> None:
    def mpesa() -> str:
        return f"QGH{secrets.token_hex(5).upper()[:7]}"

    def mixx() -> str:
        return f"MIX{utcnow().strftime('%y%m%d')}{secrets.token_hex(2).upper()}"

    def airtel() -> str:
        return f"AM{utcnow().strftime('%Y%m%d')}{secrets.randbelow(999999):06d}"

    def halopesa() -> str:
        return f"HLP-{secrets.token_hex(4).upper()}"

    def azampesa() -> str:
        return f"AZP{utcnow().strftime('%y%m%d')}{secrets.token_hex(3).upper()}"

    def selcom() -> str:
        return f"SLC-{utcnow().strftime('%Y%m%d')}-{secrets.token_hex(3).upper()}"

    _REF_GENERATORS.update({
        PaymentMethod.MPESA.value: mpesa,
        PaymentMethod.MIXX.value: mixx,
        PaymentMethod.AIRTEL_MONEY.value: airtel,
        PaymentMethod.HALOPESA.value: halopesa,
        PaymentMethod.AZAMPESA.value: azampesa,
        PaymentMethod.SELCOM_PAY.value: selcom,
    })


_register_generators()


def generate_transaction_reference(method: str) -> str:
    """Generate a realistic simulated transaction ID for the given provider."""
    generator = _REF_GENERATORS.get(method)
    if generator:
        return generator()
    return f"MED-{utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"


def _display_name(doctor: Doctor) -> str:
    name = doctor.user.full_name if doctor.user else f"Doctor #{doctor.id}"
    if not name.startswith("Dr."):
        return f"Dr. {name}"
    return name


def _get_appointment(
    db: Session,
    patient_id: int,
    appointment_id: int,
    *,
    for_update: bool = False,
) -> Appointment | None:
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(Doctor.user),
            joinedload(Appointment.doctor).joinedload(Doctor.specialization),
            joinedload(Appointment.payment),
        )
        .where(Appointment.id == appointment_id, Appointment.patient_id == patient_id)
    )
    if for_update:
        stmt = stmt.with_for_update()
    return db.scalar(stmt)


def _ensure_pending_payment(db: Session, appointment: Appointment) -> Payment | None:
    """Create a pending payment row for legacy bookings that skipped payment setup."""
    if appointment.payment:
        return appointment.payment

    if appointment.status not in (
        AppointmentStatus.PENDING.value,
        AppointmentStatus.SCHEDULED.value,
    ):
        return None

    doctor = appointment.doctor
    if not doctor:
        return None

    payment = Payment(
        appointment_id=appointment.id,
        amount=doctor.consultation_fee,
        currency=doctor.currency,
        status=PaymentStatus.PENDING.value,
        reference_number=f"MED-PEND-{appointment.id:06d}",
        phone_number=appointment.patient.phone if appointment.patient else None,
    )
    db.add(payment)
    db.commit()
    db.refresh(appointment)
    return appointment.payment


def get_payment_context(db: Session, patient_id: int, appointment_id: int) -> PaymentContext | None:
    appointment = _get_appointment(db, patient_id, appointment_id)
    if not appointment:
        return None

    if not appointment.payment:
        _ensure_pending_payment(db, appointment)
        appointment = _get_appointment(db, patient_id, appointment_id)
        if not appointment or not appointment.payment:
            return None

    doctor = appointment.doctor
    start = ensure_utc(appointment.scheduled_start)
    end = ensure_utc(appointment.scheduled_end)
    spec = doctor.specialization.name if doctor and doctor.specialization else "General"
    payment = appointment.payment

    return PaymentContext(
        appointment_id=appointment.id,
        doctor_name=_display_name(doctor) if doctor else "Unknown",
        department=spec,
        date_label=start.strftime("%A, %d %B %Y"),
        time_range=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
        amount=float(payment.amount),
        currency=payment.currency,
        status=appointment.status,
        status_label=STATUS_LABELS.get(appointment.status, appointment.status.title()),
        payment_status=payment.status,
        payment_status_label=PAYMENT_STATUS_LABELS.get(payment.status, payment.status.title()),
        methods=PAYMENT_METHODS,
    )


def get_confirmation_context(
    db: Session,
    patient_id: int,
    appointment_id: int,
) -> ConfirmationContext | None:
    appointment = _get_appointment(db, patient_id, appointment_id)
    if not appointment or not appointment.payment:
        return None

    payment = appointment.payment
    if payment.status != PaymentStatus.COMPLETED.value:
        return None

    doctor = appointment.doctor
    start = ensure_utc(appointment.scheduled_start)
    end = ensure_utc(appointment.scheduled_end)
    spec = doctor.specialization.name if doctor and doctor.specialization else "General"
    paid_at = ensure_utc(payment.paid_at) if payment.paid_at else utcnow()

    return ConfirmationContext(
        appointment_id=appointment.id,
        doctor_name=_display_name(doctor) if doctor else "Unknown",
        department=spec,
        specialization=spec,
        hospital=doctor.hospital_name if doctor else "",
        date_label=start.strftime("%A, %d %B %Y"),
        time_range=f"{start.strftime('%H:%M')} - {end.strftime('%H:%M')}",
        consultation_fee=float(payment.amount),
        currency=payment.currency,
        status=appointment.status,
        status_label=STATUS_LABELS.get(appointment.status, appointment.status.title()),
        patient_notes=appointment.patient_notes,
        reference_number=payment.reference_number,
        payment_method=payment.payment_method,
        payment_method_label=METHOD_LABELS.get(payment.payment_method, payment.payment_method),
        payment_status=payment.status,
        payment_status_label=PAYMENT_STATUS_LABELS.get(payment.status, payment.status.title()),
        paid_at=paid_at.isoformat(),
        dashboard_url="/patient/dashboard",
    )


def initiate_payment(
    db: Session,
    patient_id: int,
    appointment_id: int,
    payload: ProcessPaymentRequest,
) -> InitiatePaymentResult:
    """Mark payment as processing when the patient confirms Pay Now."""
    appointment = _get_appointment(db, patient_id, appointment_id, for_update=True)
    if not appointment:
        raise NotFoundError("Appointment not found")
    if not appointment.payment:
        _ensure_pending_payment(db, appointment)
        appointment = _get_appointment(db, patient_id, appointment_id, for_update=True)
    if not appointment or not appointment.payment:
        raise NotFoundError("Appointment not found")

    payment = appointment.payment
    if payment.status == PaymentStatus.COMPLETED.value:
        raise ConflictError("Payment has already been completed for this appointment")

    if appointment.status == AppointmentStatus.CANCELLED.value:
        raise ConflictError("Cannot pay for a cancelled appointment")

    payment.payment_method = payload.payment_method
    payment.phone_number = payload.phone_number.strip()
    payment.status = PaymentStatus.PROCESSING.value

    db.commit()

    return InitiatePaymentResult(
        appointment_id=appointment.id,
        payment_status=payment.status,
        payment_status_label=PAYMENT_STATUS_LABELS[payment.status],
        method=payload.payment_method,
        method_label=METHOD_LABELS.get(payload.payment_method, payload.payment_method),
        amount=float(payment.amount),
        currency=payment.currency,
        processing_seconds=SIMULATION_SECONDS,
    )


def complete_payment(
    db: Session,
    patient_id: int,
    appointment_id: int,
) -> PaymentResult:
    """Finalize simulated payment - generate reference, save, confirm appointment."""
    appointment = _get_appointment(db, patient_id, appointment_id, for_update=True)
    if not appointment:
        raise NotFoundError("Appointment not found")
    if not appointment.payment:
        _ensure_pending_payment(db, appointment)
        appointment = _get_appointment(db, patient_id, appointment_id, for_update=True)
    if not appointment or not appointment.payment:
        raise NotFoundError("Appointment not found")

    payment = appointment.payment

    if payment.status == PaymentStatus.COMPLETED.value:
        paid_at = ensure_utc(payment.paid_at) if payment.paid_at else utcnow()
        return PaymentResult(
            success=True,
            reference_number=payment.reference_number,
            amount=float(payment.amount),
            currency=payment.currency,
            method=payment.payment_method,
            method_label=METHOD_LABELS.get(payment.payment_method, payment.payment_method),
            appointment_id=appointment.id,
            status=appointment.status,
            status_label=STATUS_LABELS.get(appointment.status, appointment.status.title()),
            payment_status=payment.status,
            payment_status_label=PAYMENT_STATUS_LABELS[payment.status],
            paid_at=paid_at.isoformat(),
            confirmation_url=f"/appointments/confirmation/{appointment.id}",
            dashboard_url="/patient/dashboard",
        )

    if payment.status not in (
        PaymentStatus.PROCESSING.value,
        PaymentStatus.PENDING.value,
    ):
        raise ConflictError("Payment cannot be completed in its current state")

    reference = generate_transaction_reference(payment.payment_method)
    now = utcnow()

    payment.status = PaymentStatus.COMPLETED.value
    payment.reference_number = reference
    payment.paid_at = now

    previous_status = appointment.status
    if appointment.status == AppointmentStatus.PENDING.value:
        appointment.status = AppointmentStatus.CONFIRMED.value

    db.add(
        AppointmentStatusHistory(
            appointment_id=appointment.id,
            status=appointment.status,
            changed_by_user_id=patient_id,
            notes="Payment completed - appointment confirmed",
        )
    )

    if previous_status != appointment.status:
        db.add(
            Notification(
                user_id=patient_id,
                appointment_id=appointment.id,
                notification_type=NotificationType.BOOKING_CONFIRMED.value,
                channel=NotificationChannel.WEB.value,
                title="Booking confirmed",
                message=(
                    f"Your appointment with {_display_name(appointment.doctor)} "
                    f"is confirmed. Reference: {reference}"
                ),
                is_read=False,
                sent_at=now,
            )
        )
        db.add(
            Notification(
                user_id=patient_id,
                appointment_id=appointment.id,
                notification_type=NotificationType.PAYMENT_SUCCESS.value,
                channel=NotificationChannel.WEB.value,
                title="Payment received",
                message=f"We received your {METHOD_LABELS.get(payment.payment_method, 'payment')}. Reference: {reference}",
                is_read=False,
                sent_at=now,
            )
        )

    db.commit()

    return PaymentResult(
        success=True,
        reference_number=reference,
        amount=float(payment.amount),
        currency=payment.currency,
        method=payment.payment_method,
        method_label=METHOD_LABELS.get(payment.payment_method, payment.payment_method),
        appointment_id=appointment.id,
        status=appointment.status,
        status_label=STATUS_LABELS.get(appointment.status, appointment.status.title()),
        payment_status=payment.status,
        payment_status_label=PAYMENT_STATUS_LABELS[payment.status],
        paid_at=now.isoformat(),
        confirmation_url=f"/appointments/confirmation/{appointment.id}",
        dashboard_url="/patient/dashboard",
    )


def process_payment(
    db: Session,
    patient_id: int,
    appointment_id: int,
    payload: ProcessPaymentRequest,
) -> PaymentResult:
    """One-shot payment (initiate + complete) - kept for backward compatibility."""
    initiate_payment(db, patient_id, appointment_id, payload)
    return complete_payment(db, patient_id, appointment_id)
