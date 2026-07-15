"""Send a one-off KilaKona SMS using credentials from .env.

Aligned with: https://messaging.kilakona.co.tz/api-documentation

Usage (from project root):
  python scripts/test_sms.py 2557XXXXXXXX
  python scripts/test_sms.py 07XXXXXXXX "Custom test message"
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.services import sms_service


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_sms.py <phone> [message]")
        print("Example: python scripts/test_sms.py 255712345678")
        return 1

    phone = sys.argv[1]
    message = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "mediBook test SMS from KilaKona integration."
    )

    get_settings.cache_clear()
    settings = get_settings()
    contact = sms_service.normalize_phone(phone)

    print("--- KilaKona docs checklist ---")
    print("Endpoint:", settings.sms_api_url)
    print("Headers: api_key / api_secret / Content-Type=application/json")
    print("SMS_API_KEY set:", bool(settings.sms_api_key))
    print("SMS_API_SECRET set:", bool(settings.sms_api_secret))
    print("SMS_SENDER_ID:", settings.sms_sender_id or "(REQUIRED by docs - missing)")
    print(
        "SMS_DELIVERY_REPORT_URL:",
        settings.sms_delivery_report_url or "(empty OK on localhost)",
    )
    print("Configured (key+secret+senderId):", sms_service.is_sms_configured())
    print("Normalized contacts:", contact)
    if contact and sms_service.is_sms_configured():
        print(
            "Payload preview:",
            json.dumps(sms_service._build_payload(contact=contact, message=message), indent=2),
        )
    print("Sending...")

    ok = sms_service.send_sms(to_phone=phone, message=message)
    if ok and sms_service.is_sms_configured():
        print("SUCCESS - submitted (success=true). Check phone + KilaKona portal / shootId in logs.")
        return 0
    if ok and not sms_service.is_sms_configured():
        print(
            "SIMULATION only. Fill ALL of these in .env then rerun:\n"
            "  SMS_API_KEY=\n"
            "  SMS_API_SECRET=\n"
            "  SMS_SENDER_ID=   # from KilaKona portal (docs require this)\n"
            "Leave SMS_DELIVERY_REPORT_URL empty on localhost."
        )
        return 2
    print("FAILED - see error log. Confirm key, secret, senderId, credits, and phone format.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
