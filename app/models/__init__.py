"""SQLAlchemy ORM models - import all models so Alembic discovers metadata."""

from app.models.admin import Admin
from app.models.appointment import Appointment
from app.models.appointment_status_history import AppointmentStatusHistory
from app.models.doctor import Doctor
from app.models.doctor_availability import DoctorAvailability
from app.models.doctor_review import DoctorReview
from app.models.enums import (
    AppointmentStatus,
    AvailabilityStatus,
    Gender,
    NotificationChannel,
    NotificationType,
    PaymentMethod,
    PaymentStatus,
    UserRole,
)
from app.models.notification import Notification
from app.models.password_reset import PasswordResetToken
from app.models.payment import Payment
from app.models.specialization import Specialization
from app.models.user import User

__all__ = [
    "User",
    "Admin",
    "Doctor",
    "DoctorReview",
    "Specialization",
    "DoctorAvailability",
    "Appointment",
    "AppointmentStatusHistory",
    "Payment",
    "Notification",
    "PasswordResetToken",
    "UserRole",
    "AppointmentStatus",
    "AvailabilityStatus",
    "PaymentStatus",
    "PaymentMethod",
    "NotificationType",
    "NotificationChannel",
    "Gender",
]
