"""Check book page and API responses."""
import re
import requests

BASE = "http://127.0.0.1:8001"
s = requests.Session()
r = s.post(f"{BASE}/login", data={"email": "amina.hassan@email.com", "password": "Patient@123456"})
print("login", r.status_code)

page = s.get(f"{BASE}/appointments/book?doctor=1")
print("book page", page.status_code, len(page.text))
print("booking.js version", "FOUND" if "booking.js?v=" in page.text else "MISSING v param")
print("static_v in page", re.search(r"booking\.js\?v=([^\s\"']+)", page.text).group(1) if "booking.js?v=" in page.text else "n/a")

api = s.get(f"{BASE}/api/v1/appointments/doctors")
print("api", api.status_code, "count", len(api.json()) if api.ok else api.text[:100])

# fetch actual booking.js first lines
js = s.get(f"{BASE}/static/js/pages/booking.js")
print("booking.js served", js.status_code, "has finally", "finally" in js.text, "cache-control", js.headers.get("Cache-Control"))
