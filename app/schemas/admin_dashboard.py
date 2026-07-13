"""Admin dashboard API schemas."""

from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class AdminDashboardStats(BaseModel):
    total_doctors: int
    active_doctors: int
    total_patients: int
    active_patients: int
    today_appointments: int
    monthly_revenue: float
    currency: str
    total_appointments: int
    pending_payments: int


class ChartBarItem(BaseModel):
    label: str
    value: float
    display: str


class AdminCharts(BaseModel):
    appointments_per_month: list[ChartBarItem]
    payments_per_month: list[ChartBarItem]
    doctor_distribution: list[ChartBarItem]


class AdminDashboardOverview(BaseModel):
    greeting: str
    admin_name: str
    department: str
    job_title: str
    stats: AdminDashboardStats
    charts: AdminCharts


class AdminDoctorItem(BaseModel):
    id: int
    user_id: int
    name: str
    first_name: str
    last_name: str
    email: str
    phone: str | None
    specialization: str
    specialization_id: int
    hospital: str
    license_number: str
    consultation_fee: float
    currency: str
    experience_years: int
    is_verified: bool
    is_accepting_patients: bool
    is_active: bool
    appointment_count: int


class CreateDoctorRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str | None = Field(None, max_length=20)
    password: str = Field(..., min_length=8, max_length=128)
    specialization_id: int
    license_number: str = Field(..., min_length=3, max_length=60)
    hospital_name: str = Field(..., min_length=2, max_length=200)
    consultation_fee: float = Field(..., ge=0)
    experience_years: int = Field(0, ge=0)
    qualification: str | None = Field(None, max_length=200)
    is_verified: bool = True
    is_accepting_patients: bool = True


class UpdateDoctorRequest(BaseModel):
    first_name: str | None = Field(None, min_length=2, max_length=100)
    last_name: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=20)
    specialization_id: int | None = None
    hospital_name: str | None = Field(None, max_length=200)
    consultation_fee: float | None = Field(None, ge=0)
    experience_years: int | None = Field(None, ge=0)
    qualification: str | None = Field(None, max_length=200)
    is_verified: bool | None = None
    is_accepting_patients: bool | None = None


class AdminPatientItem(BaseModel):
    id: int
    name: str
    email: str
    phone: str | None
    is_active: bool
    appointment_count: int
    joined_at: str


class AdminAppointmentItem(BaseModel):
    id: int
    patient_name: str
    doctor_name: str
    specialization: str
    scheduled_start: str
    date_label: str
    time_range: str
    status: str
    status_label: str
    payment_status: str | None


class AdminPaymentItem(BaseModel):
    id: int
    appointment_id: int
    patient_name: str
    doctor_name: str
    amount: float
    currency: str
    method: str
    method_label: str
    status: str
    status_label: str
    reference_number: str
    paid_at: str | None


class AdminNotificationItem(BaseModel):
    id: int
    user_name: str
    type: str
    channel: str
    title: str
    message: str
    is_read: bool
    created_at: str


class ChartPieItem(BaseModel):
    label: str
    value: float
    display: str


class AdminReportCharts(BaseModel):
    appointment_status: list[ChartPieItem]
    payment_methods: list[ChartPieItem]
    appointments_trend: list[ChartBarItem]
    revenue_trend: list[ChartBarItem]
    doctor_distribution: list[ChartBarItem]
    growth_comparison: list[ChartBarItem]


class AdminReportSummary(BaseModel):
    period_label: str
    total_appointments: int
    completed_appointments: int
    cancelled_appointments: int
    total_revenue: float
    currency: str
    new_patients: int
    new_doctors: int
    charts: AdminReportCharts
    export_ready: bool = True
    generated_at: str


class AdminSettingsView(BaseModel):
    app_name: str
    environment: str
    reminder_enabled: bool
    reminder_check_interval_minutes: int
    reminder_hours_before: int
    email_reminders_enabled: bool
    currency: str


class SpecializationOption(BaseModel):
    id: int
    name: str
    slug: str
