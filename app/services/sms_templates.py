"""Warm, bilingual appointment SMS bodies for patients."""

from __future__ import annotations

from datetime import datetime

from app.config import get_settings
from app.models import User
from app.services.sms_service import sanitize_sms_text
from app.utils.helpers import ensure_utc

SW_WEEKDAYS = (
    "Jumatatu",
    "Jumanne",
    "Jumatano",
    "Alhamisi",
    "Ijumaa",
    "Jumamosi",
    "Jumapili",
)
SW_MONTHS = (
    "",
    "Januari",
    "Februari",
    "Machi",
    "Aprili",
    "Mei",
    "Juni",
    "Julai",
    "Agosti",
    "Septemba",
    "Oktoba",
    "Novemba",
    "Desemba",
)


def resolve_sms_language(patient: User) -> str:
    """Language for SMS: patient preference -> app default -> sw."""
    preferred = (getattr(patient, "preferred_language", None) or "").strip().lower()
    if preferred in {"sw", "en"}:
        return preferred
    fallback = (get_settings().sms_default_language or "sw").strip().lower()
    return fallback if fallback in {"sw", "en"} else "sw"


def _day_period(hour: int, lang: str) -> str:
    if 5 <= hour < 12:
        return "asubuhi" if lang == "sw" else "in the morning"
    if 12 <= hour < 17:
        return "mchana" if lang == "sw" else "in the afternoon"
    if 17 <= hour < 21:
        return "jioni" if lang == "sw" else "in the evening"
    return "usiku" if lang == "sw" else "at night"


def _format_date_sw(dt: datetime) -> str:
    return f"{SW_WEEKDAYS[dt.weekday()]}, {dt.day} {SW_MONTHS[dt.month]} {dt.year}"


def _format_date_en(dt: datetime) -> str:
    return dt.strftime("%A, %d %B %Y")


def _when_phrase(hours_before: int, lang: str) -> str:
    if hours_before >= 24:
        return "kesho" if lang == "sw" else "tomorrow"
    if hours_before >= 2:
        return "leo hivi (ndani ya saa 2)" if lang == "sw" else "very soon (within 2 hours)"
    return (
        f"hivi punde (ndani ya saa {hours_before})"
        if lang == "sw"
        else f"very soon (within {hours_before} hours)"
    )


def format_sms_reminder(
    patient: User,
    *,
    doctor_name: str,
    department: str,
    hours_before: int,
    scheduled_start: datetime,
) -> str:
    """Friendly reminder SMS (Swahili or English)."""
    lang = resolve_sms_language(patient)
    start = ensure_utc(scheduled_start)
    first = (patient.first_name or "").strip()
    if not first:
        first = "ndugu mteja" if lang == "sw" else "there"

    when = _when_phrase(hours_before, lang)
    period = _day_period(start.hour, lang)
    time_label = start.strftime("%H:%M")

    if lang == "en":
        date_label = _format_date_en(start)
        return sanitize_sms_text(
            "mediBook\n\n"
            f"Hi {first},\n\n"
            f"This is a gentle reminder that you have an appointment with "
            f"{doctor_name} ({department}) {when}, "
            f"{date_label} at {time_label} {period}.\n\n"
            "Please arrive about 10 minutes early so we can take good care of you.\n\n"
            "You are warmly welcome!"
        )

    date_label = _format_date_sw(start)
    return sanitize_sms_text(
        "mediBook\n\n"
        f"Habari {first},\n\n"
        f"Hii ni kukumbusha kuwa una miadi na {doctor_name} "
        f"({department}) {when}, {date_label} saa {time_label} {period}.\n\n"
        "Tafadhali fika mapema kidogo (kama dakika 10 kabla) ili tukuhudumie vizuri.\n\n"
        "Karibu sana!"
    )


def _money_label(amount: float, currency: str, lang: str) -> str:
    cur = (currency or "TZS").upper()
    if cur in {"TZS", "TSH", "TANZANIAN SHILLING"}:
        return f"TSh {amount:,.0f}" if lang == "sw" else f"TZS {amount:,.0f}"
    return f"{cur} {amount:,.2f}"


def format_payment_success_sms(
    patient: User,
    *,
    doctor_name: str,
    department: str,
    scheduled_start: datetime,
    amount: float,
    currency: str,
    reference: str,
    method_label: str,
) -> str:
    """One professional SMS: payment received + booking confirmed (saves credits)."""
    lang = resolve_sms_language(patient)
    start = ensure_utc(scheduled_start)
    first = (patient.first_name or "").strip()
    if not first:
        first = "ndugu mteja" if lang == "sw" else "there"

    period = _day_period(start.hour, lang)
    time_label = start.strftime("%H:%M")
    money = _money_label(amount, currency, lang)
    method = method_label or ("malipo" if lang == "sw" else "payment")

    if lang == "en":
        date_label = _format_date_en(start)
        return sanitize_sms_text(
            "mediBook\n\n"
            f"Hi {first},\n\n"
            f"Payment received via {method} ({money}). Ref: {reference}.\n\n"
            f"Your appointment with {doctor_name} ({department}) is confirmed for "
            f"{date_label} at {time_label} {period}.\n\n"
            "Thank you for choosing mediBook. We look forward to seeing you."
        )

    date_label = _format_date_sw(start)
    return sanitize_sms_text(
        "mediBook\n\n"
        f"Habari {first},\n\n"
        f"Malipo yako kwa {method} yamepokelewa ({money}). Kumbukumbu: {reference}.\n\n"
        f"Miadi yako na {doctor_name} ({department}) imethibitishwa: "
        f"{date_label} saa {time_label} {period}.\n\n"
        "Asante kwa kuchagua mediBook. Karibu sana!"
    )


def format_doctor_confirm_sms(
    patient: User,
    *,
    doctor_name: str,
    department: str,
    scheduled_start: datetime,
) -> str:
    """Warm SMS when a doctor approves/confirms the appointment."""
    lang = resolve_sms_language(patient)
    start = ensure_utc(scheduled_start)
    first = (patient.first_name or "").strip()
    if not first:
        first = "ndugu mteja" if lang == "sw" else "there"

    period = _day_period(start.hour, lang)
    time_label = start.strftime("%H:%M")

    if lang == "en":
        date_label = _format_date_en(start)
        return sanitize_sms_text(
            "mediBook\n\n"
            f"Hi {first},\n\n"
            f"Good news - {doctor_name} ({department}) has confirmed your appointment "
            f"for {date_label} at {time_label} {period}.\n\n"
            "Please arrive about 10 minutes early. We look forward to seeing you."
        )

    date_label = _format_date_sw(start)
    return sanitize_sms_text(
        "mediBook\n\n"
        f"Habari {first},\n\n"
        f"Habari njema - {doctor_name} ({department}) amethibitisha miadi yako "
        f"tarehe {date_label} saa {time_label} {period}.\n\n"
        "Tafadhali fika dakika 10 mapema. Karibu sana!"
    )
