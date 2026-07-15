"""SMS dispatch via KilaKona - aligned with official API docs.

Docs: https://messaging.kilakona.co.tz/api-documentation

POST /api/v1/vendor/message/send
Headers: api_key, api_secret, Content-Type: application/json
Body: senderId, messageType, message, contacts, deliveryReportUrl
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_SMS_API_URL = "https://messaging.kilakona.co.tz/api/v1/vendor/message/send"

# 1:1 replacements for characters that often corrupt on SMS gateways / handsets
_SMS_CHAR_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201a": "'",
        "\u201b": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u00a0": " ",
        "\u00ad": "",
        "\ufeff": "",
    }
)


def sanitize_sms_text(message: str) -> str:
    """Normalize SMS body to avoid mojibake / UCS-2 corruption on handsets."""
    if not message:
        return ""

    text = unicodedata.normalize("NFKC", message)
    text = (
        text.replace("\u2026", "...")
        .replace("\u2192", "->")
        .replace("\u2190", "<-")
    )
    text = text.translate(_SMS_CHAR_MAP)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        ch for ch in text if ch in "\n\t" or (ord(ch) >= 32 and ord(ch) != 127)
    )
    # Keep latin-1; replace anything else so gateway stays on simple encoding
    return "".join(ch if ord(ch) <= 255 else "?" for ch in text).strip()


def is_sms_configured() -> bool:
    """True when docs-required credentials are present (key, secret, senderId)."""
    settings = get_settings()
    return bool(
        (settings.sms_api_url or DEFAULT_SMS_API_URL)
        and settings.sms_api_key
        and settings.sms_api_secret
        and settings.sms_sender_id
    )


def normalize_phone(phone: str) -> str | None:
    """Normalize numbers to digits (TZ: 07... / 255... / 7...)."""
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return None

    if digits.startswith("0") and len(digits) == 10:
        digits = "255" + digits[1:]
    elif digits.startswith("255") and len(digits) >= 12:
        pass
    elif len(digits) == 9 and digits[0] in "67":
        digits = "255" + digits

    if len(digits) < 9:
        return None
    return digits


def _build_payload(*, contact: str, message: str) -> dict[str, str]:
    """Build request body exactly as documented."""
    settings = get_settings()
    return {
        "senderId": (settings.sms_sender_id or "").strip(),
        "messageType": "text",
        "message": message,
        "contacts": contact,
        "deliveryReportUrl": (settings.sms_delivery_report_url or "").strip(),
    }


def _is_success_response(status_code: int, body: Any) -> bool:
    """Accept only documented success shape: HTTP 200 + success true (+ valid contact)."""
    if status_code != 200 or not isinstance(body, dict):
        return False
    if body.get("success") is not True:
        return False
    code = body.get("code")
    if code is not None and code != 200:
        return False

    data = body.get("data")
    if isinstance(data, dict) and "validContacts" in data:
        try:
            return int(data["validContacts"]) >= 1
        except (TypeError, ValueError):
            return False
    return True


def send_sms(*, to_phone: str, message: str) -> bool:
    """Send an SMS via KilaKona. Returns True when submit succeeds per docs.

    Callers decide enable/disable (payment / reminder / doctor-confirm).
    This function only delivers; it sanitizes text then POSTs.
    """
    settings = get_settings()
    safe_message = sanitize_sms_text(message)

    contact = normalize_phone(to_phone)
    if not contact:
        logger.warning("SMS skipped - invalid phone: %r", to_phone)
        return False

    if not safe_message:
        logger.warning("SMS skipped - empty message after sanitize")
        return False

    if not is_sms_configured():
        preview = safe_message[:200] + ("..." if len(safe_message) > 200 else "")
        logger.info("[SMS SIMULATION] To: %s | Message: %s", contact, preview)
        return True

    api_url = (settings.sms_api_url or DEFAULT_SMS_API_URL).strip()
    payload = _build_payload(contact=contact, message=safe_message)
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "api_key": settings.sms_api_key or "",
        "api_secret": settings.sms_api_secret or "",
        "Accept": "application/json",
    }

    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=20,
        )
        try:
            body: Any = response.json()
        except ValueError:
            body = {"raw": response.text[:500]}

        if _is_success_response(response.status_code, body):
            data = body.get("data") if isinstance(body, dict) else None
            shoot_id = data.get("shootId") if isinstance(data, dict) else None
            logger.info(
                "SMS sent to %s via KilaKona (shootId=%s validContacts=%s)",
                contact,
                shoot_id,
                data.get("validContacts") if isinstance(data, dict) else None,
            )
            return True

        logger.error(
            "KilaKona SMS failed for %s - status=%s body=%s",
            contact,
            response.status_code,
            body,
        )
        return False
    except requests.RequestException:
        logger.exception("KilaKona SMS request error for %s", contact)
        return False
