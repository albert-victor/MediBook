# mediBook - Medical Appointment & Reminder System

A production-oriented healthcare platform for booking appointments, managing doctors and patients, processing simulated payments, and sending automated reminders.

**Stack:** FastAPI · SQLAlchemy · SQLite (MySQL-ready) · Jinja2 · Vanilla JavaScript · Bootstrap Icons

**Languages:** English (default) · Kiswahili (client-side i18n)

---

## Features

- Public landing page, doctor directory, services catalogue
- Multi-step appointment booking with real-time slot availability
- Simulated mobile money payments (M-Pesa, Mixx, Airtel Money, etc.)
- Automated appointment reminders (email + web notifications)
- Role-based dashboards: **Patient**, **Doctor**, **Administrator**
- Bilingual UI with instant language switching (EN / SW)

---

## Quick Start

### 1. Virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment

```bash
copy .env.example .env
```

Set a secure `SECRET_KEY` in `.env`.

### 4. Database & seed data

```bash
python scripts/seed.py
```

### 5. Run

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

| URL | Description |
|-----|-------------|
| http://127.0.0.1:8001 | Landing page |
| http://127.0.0.1:8001/api/docs | OpenAPI docs |
| http://127.0.0.1:8001/patient/dashboard | Patient dashboard |
| http://127.0.0.1:8001/doctor/dashboard | Doctor dashboard |
| http://127.0.0.1:8001/admin/dashboard | Admin dashboard |

### Demo logins

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@medcare.com | Admin@123456 |
| Doctor | s.okello@medcare.com | Doctor@123456 |
| Patient | amina.hassan@email.com | Patient@123456 |

---

## Project Structure

See **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** for the full layout, request flow, and architecture.

```
appointment/
├── app/           # Backend (API, services, auth, models)
├── templates/     # Jinja2 HTML
├── static/        # CSS, JS, i18n locales
├── scripts/       # Seeders, RBAC test, locale generator
├── docs/          # MySQL schema, structure docs
└── data/          # SQLite database (gitignored)
```

---

## Architecture

- **Single origin** - FastAPI serves API + frontend together
- **Service layer** - Routes stay thin; logic in `app/services/`
- **Session auth** - Cookie-based sessions with role guards (web + API)
- **i18n** - `static/js/i18n/` with JSON locales; `data-i18n` in templates
- **MySQL-ready** - Portable SQLAlchemy types; see `docs/mysql_schema.sql`
- **Reminders** - APScheduler in-process (swap for worker in production)

---

## Development

### Role isolation test

```bash
python scripts/test_rbac.py
```

### Regenerate locale files

```bash
python scripts/generate_locales.py
```

### Design rules

See [`cursor/project_rules.md`](cursor/project_rules.md) for UI philosophy, animation standards, and coding conventions.

---

## API overview

| Prefix | Auth | Purpose |
|--------|------|---------|
| `/api/v1/patient/` | Patient | Dashboard, appointments, payments |
| `/api/v1/doctor/` | Doctor | Practice management, calendar |
| `/api/v1/admin/` | Admin | Platform management, analytics |
| `/api/v1/doctors/` | Public | Doctor directory |
| `/api/v1/appointments/` | Patient | Booking engine |
| `/api/v1/payments/` | Patient | Payment simulation |

---

## License

Internal / educational use. See project documentation for deployment notes.
