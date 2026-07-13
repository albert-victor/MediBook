"""Quick RBAC smoke test - run: python scripts/test_rbac.py"""
import requests

BASE = "http://127.0.0.1:8001"

ACCOUNTS = [
    ("admin@medcare.com", "Admin@123456", "admin"),
    ("s.okello@medcare.com", "Doctor@123456", "doctor"),
    ("amina.hassan@email.com", "Patient@123456", "patient"),
]

DASHBOARDS = {
    "patient": "/patient/dashboard",
    "doctor": "/doctor/dashboard",
    "admin": "/admin/dashboard",
}

APIS = {
    "patient": "/api/v1/patient/dashboard/overview",
    "doctor": "/api/v1/doctor/dashboard/overview",
    "admin": "/api/v1/admin/dashboard/overview",
}


def login(email: str, password: str, next_url: str = "") -> requests.Session:
    s = requests.Session()
    data = {"email": email, "password": password}
    if next_url:
        data["next"] = next_url
    s.post(f"{BASE}/login", data=data, allow_redirects=False)
    return s


def test_login_redirects() -> None:
    print("\n=== Login redirects (default next) ===")
    expected = {
        "admin@medcare.com": "/admin/dashboard",
        "s.okello@medcare.com": "/doctor/dashboard",
        "amina.hassan@email.com": "/patient/dashboard",
    }
    for email, password, role in ACCOUNTS:
        r = requests.post(
            f"{BASE}/login",
            data={"email": email, "password": password, "next": "/"},
            allow_redirects=False,
        )
        loc = r.headers.get("location", "")
        exp = expected[email]
        status = "OK" if loc == exp else "FAIL"
        print(f"  {role} next=/: {r.status_code} -> {loc} (expected {exp}) [{status}]")


def test_home_redirect_when_logged_in() -> None:
    print("\n=== Home redirect when logged in ===")
    expected = {
        "admin@medcare.com": "/admin/dashboard",
        "s.okello@medcare.com": "/doctor/dashboard",
        "amina.hassan@email.com": "/patient/dashboard",
    }
    for email, password, role in ACCOUNTS:
        s = login(email, password)
        r = s.get(f"{BASE}/", allow_redirects=False)
        loc = r.headers.get("location", "")
        exp = expected[email]
        status = "OK" if r.status_code == 303 and loc == exp else "FAIL"
        print(f"  {role} GET /: {r.status_code} -> {loc} (expected {exp}) [{status}]")


def main() -> None:
    test_login_redirects()
    test_home_redirect_when_logged_in()
    for email, password, role in ACCOUNTS:
        s = login(email, password)
        print(f"\n=== {role} ({email}) ===")
        for target, path in DASHBOARDS.items():
            r = s.get(f"{BASE}{path}", allow_redirects=False)
            allowed = role == target
            status = "OK" if (allowed and r.status_code == 200) or (not allowed and r.status_code in (303, 307)) else "FAIL"
            print(f"  HTML {path}: {r.status_code} -> {r.headers.get('location', 'page')} [{status}]")
        for target, path in APIS.items():
            r = s.get(f"{BASE}{path}")
            allowed = role == target
            status = "OK" if (allowed and r.status_code == 200) or (not allowed and r.status_code == 403) else "FAIL"
            print(f"  API  {path}: {r.status_code} [{status}]")


if __name__ == "__main__":
    main()
