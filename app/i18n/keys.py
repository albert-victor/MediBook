"""Localization-ready message keys for API responses.

Frontend maps these keys via api.* entries in locale JSON files.
Future: resolve keys server-side using Accept-Language header.
"""

from enum import Enum


class MessageKey(str, Enum):
    NOT_AUTHENTICATED = "api.notAuthenticated"
    PATIENTS_ONLY = "api.patientsOnly"
    DOCTORS_ONLY = "api.doctorsOnly"
    ADMINS_ONLY = "api.adminsOnly"
    NOT_FOUND = "api.notFound"
    APPOINTMENT_NOT_FOUND = "api.appointmentNotFound"
    DOCTOR_NOT_FOUND = "api.doctorNotFound"
    NOTIFICATION_NOT_FOUND = "api.notificationNotFound"
    SLOT_ALREADY_BOOKED = "api.slotAlreadyBooked"
    EMAIL_EXISTS = "api.emailExists"
    LICENSE_EXISTS = "api.licenseExists"
    DOCTOR_HAS_APPOINTMENTS = "api.doctorHasAppointments"
    PAYMENT_PENDING = "api.paymentPending"


# Legacy plain-text messages → i18n keys (for gradual migration)
_LEGACY_MAP: dict[str, MessageKey] = {
    "Not authenticated": MessageKey.NOT_AUTHENTICATED,
    "Patients only": MessageKey.PATIENTS_ONLY,
    "Doctors only": MessageKey.DOCTORS_ONLY,
    "Admins only": MessageKey.ADMINS_ONLY,
    "Appointment not found": MessageKey.APPOINTMENT_NOT_FOUND,
    "Doctor not found": MessageKey.DOCTOR_NOT_FOUND,
    "Notification not found": MessageKey.NOTIFICATION_NOT_FOUND,
    "This appointment slot has already been booked. Please choose another available time.": MessageKey.SLOT_ALREADY_BOOKED,
    "A user with this email already exists": MessageKey.EMAIL_EXISTS,
    "License number already registered": MessageKey.LICENSE_EXISTS,
}


def get_message_key(message: str) -> str | None:
    """Return i18n key for a legacy message, if mapped."""
    key = _LEGACY_MAP.get(message)
    return key.value if key else None
