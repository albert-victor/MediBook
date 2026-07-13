"""Appointment booking API schemas."""

from pydantic import BaseModel, Field


SLOT_CONFLICT_MESSAGE = (
    "This appointment slot has already been booked. "
    "Please choose another available time."
)


class BookingSlot(BaseModel):
    id: int
    date: str
    start_time: str
    end_time: str
    status: str
    is_available: bool


class BookingDoctor(BaseModel):
    id: int
    name: str
    specialization: str
    department: str
    hospital: str
    fee: float
    currency: str
    initials: str
    avatar_gradient: str
    image_url: str | None
    is_accepting_patients: bool


class BookingSummary(BaseModel):
    appointment_id: int
    doctor_name: str
    department: str
    specialization: str
    hospital: str
    date: str
    date_label: str
    time: str
    time_range: str
    consultation_fee: float
    currency: str
    status: str
    status_label: str
    patient_notes: str | None
    payment_url: str


class CreateBookingRequest(BaseModel):
    doctor_id: int
    availability_id: int
    patient_notes: str | None = Field(None, max_length=1000)


class PaymentMethodOption(BaseModel):
    id: str
    label: str
    icon: str


class PaymentContext(BaseModel):
    appointment_id: int
    doctor_name: str
    department: str
    date_label: str
    time_range: str
    amount: float
    currency: str
    status: str
    status_label: str
    payment_status: str | None
    payment_status_label: str | None
    methods: list[PaymentMethodOption]


class ProcessPaymentRequest(BaseModel):
    payment_method: str = Field(..., pattern="^(mpesa|mixx|airtel_money|halopesa|azampesa|selcom_pay)$")
    phone_number: str = Field(..., min_length=9, max_length=15)


class PaymentResult(BaseModel):
    success: bool
    reference_number: str
    amount: float
    currency: str
    method: str
    method_label: str
    appointment_id: int
    status: str
    status_label: str
    payment_status: str
    payment_status_label: str
    paid_at: str
    confirmation_url: str
    dashboard_url: str


class InitiatePaymentResult(BaseModel):
    appointment_id: int
    payment_status: str
    payment_status_label: str
    method: str
    method_label: str
    amount: float
    currency: str
    processing_seconds: int = 6


class ConfirmationContext(BaseModel):
    appointment_id: int
    doctor_name: str
    department: str
    specialization: str
    hospital: str
    date_label: str
    time_range: str
    consultation_fee: float
    currency: str
    status: str
    status_label: str
    patient_notes: str | None
    reference_number: str
    payment_method: str
    payment_method_label: str
    payment_status: str
    payment_status_label: str
    paid_at: str
    dashboard_url: str
