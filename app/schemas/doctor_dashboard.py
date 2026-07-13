"""Doctor dashboard API response schemas."""

from pydantic import BaseModel, Field


class DoctorDashboardStats(BaseModel):
    today: int
    upcoming: int
    completed: int
    cancelled: int
    total_patients: int
    pending_approval: int


class DoctorDashboardOverview(BaseModel):
    greeting: str
    doctor_name: str
    specialization: str
    hospital: str
    stats: DoctorDashboardStats
    profile_url: str


class DoctorAppointmentItem(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    patient_initials: str
    patient_phone: str | None
    patient_email: str
    scheduled_start: str
    scheduled_end: str
    date_label: str
    time_range: str
    status: str
    status_label: str
    patient_notes: str | None
    payment_status: str | None
    cancellation_reason: str | None = None


class DoctorPatientBrief(BaseModel):
    id: int
    name: str
    initials: str
    phone: str | None
    email: str
    total_visits: int
    last_visit: str | None


class DoctorPatientDetail(DoctorPatientBrief):
    upcoming_visits: int
    completed_visits: int
    recent_notes: list[str]


class DoctorActivityItem(BaseModel):
    id: int
    appointment_id: int
    patient_name: str
    status: str
    status_label: str
    notes: str | None
    created_at: str


class DoctorCalendarDay(BaseModel):
    date: str
    count: int
    label: str


class CancelAppointmentRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)
