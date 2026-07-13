"""Quick payment flow smoke test."""
import re
from datetime import date, timedelta

import requests

BASE = "http://127.0.0.1:8001"


def main() -> None:
    s = requests.Session()
    s.post(
        f"{BASE}/login",
        data={"email": "amina.hassan@email.com", "password": "Patient@123456"},
    )
    d = (date.today() + timedelta(days=3)).isoformat()
    slots = s.get(f"{BASE}/api/v1/appointments/slots?doctor_id=1&date={d}").json()
    avail = next((x for x in slots if x["is_available"]), None)
    print("slot:", avail)
    if not avail:
        print("No available slot")
        return

    book = s.post(
        f"{BASE}/api/v1/appointments",
        json={"doctor_id": 1, "availability_id": avail["id"], "patient_notes": "test"},
    )
    print("book:", book.status_code, book.text[:300])
    if not book.ok:
        return

    aid = book.json()["appointment_id"]
    pay = s.get(f"{BASE}/api/v1/payments/appointment/{aid}")
    print("pay:", pay.status_code)
    print("pay body:", pay.text[:500])
    page = s.get(f"{BASE}/appointments/payment/{aid}")
    print("page:", page.status_code)
    m = re.search(r'data-appointment-id="(\d+)"', page.text)
    print("id in page:", m.group(1) if m else None)

    # appointment without payment
    pay2 = s.get(f"{BASE}/api/v1/payments/appointment/2")
    print("pay appt2 (no payment row):", pay2.status_code, pay2.text)


if __name__ == "__main__":
    main()
