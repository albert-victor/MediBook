"""Patient dashboard API response schemas."""

from pydantic import BaseModel


class DoctorBrief(BaseModel):
    id: int
    name: str
    specialization: str
    hospital: str
    fee: float
    currency: str
    rating: float
    initials: str
    avatar_gradient: str
    available_today: bool
    profile_url: str
    book_url: str


class AppointmentItem(BaseModel):
    id: int
    doctor_name: str
    specialization: str
    hospital: str
    scheduled_start: str
    scheduled_end: str
    status: str
    status_label: str
    payment_status: str | None
    payment_url: str | None = None


class PaymentItem(BaseModel):
    id: int
    appointment_id: int
    doctor_name: str
    amount: float
    currency: str
    method: str
    method_label: str
    status: str
    status_label: str
    reference_number: str
    paid_at: str | None


class NotificationItem(BaseModel):
    id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: str
    appointment_id: int | None
    channel: str | None = None
    channel_label: str | None = None
    delivery_status: str | None = None
    delivery_status_label: str | None = None
    doctor_name: str | None = None
    department: str | None = None
    appointment_date: str | None = None
    appointment_time: str | None = None
    appointment_status: str | None = None
    appointment_status_label: str | None = None


class DashboardStats(BaseModel):
    total_appointments: int
    completed: int
    upcoming: int
    total_spent: float
    currency: str
    unread_notifications: int


class UpcomingAppointment(BaseModel):
    id: int
    doctor_name: str
    specialization: str
    hospital: str
    scheduled_start: str
    scheduled_end: str
    status: str
    status_label: str
    days_until: int
    hours_until: int


class UpcomingReminder(BaseModel):
    appointment_id: int
    title: str
    message: str
    scheduled_start: str
    channel: str


class QuickAction(BaseModel):
    label: str
    icon: str
    url: str
    color: str


class DashboardOverview(BaseModel):
    greeting: str
    patient_name: str
    stats: DashboardStats
    upcoming: UpcomingAppointment | None
    reminder: UpcomingReminder | None
    quick_actions: list[QuickAction]
