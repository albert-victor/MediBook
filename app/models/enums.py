"""Domain enumerations - string values stored in DB for MySQL/SQLite portability."""

from enum import Enum


class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    BLOCKED = "blocked"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    MPESA = "mpesa"
    MIXX = "mixx"
    AIRTEL_MONEY = "airtel_money"
    HALOPESA = "halopesa"
    AZAMPESA = "azampesa"
    SELCOM_PAY = "selcom_pay"


class NotificationType(str, Enum):
    APPOINTMENT_REMINDER = "appointment_reminder"
    BOOKING_CONFIRMED = "booking_confirmed"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    CANCELLATION = "cancellation"
    GENERAL = "general"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    WEB = "web"
    SMS = "sms"


class NotificationDeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    SKIPPED = "skipped"  # future channel placeholder (e.g. SMS not yet integrated)


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
