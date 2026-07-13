# mediBook - Project Structure

Healthcare appointment and reminder platform. FastAPI serves both the REST API and Jinja2 HTML frontend from a single origin.

## Top-level layout

```
appointment/
├── app/                        # Python application package
│   ├── main.py                 # FastAPI factory, middleware, static mount
│   ├── config/                 # Pydantic settings (.env)
│   ├── database/               # SQLAlchemy engine, session, Base
│   ├── models/                 # ORM models (SQLite / MySQL-ready)
│   ├── schemas/                # Pydantic request/response DTOs
│   ├── services/               # Business logic (single responsibility)
│   ├── api/v1/                 # JSON REST endpoints
│   ├── routes/                 # Server-rendered HTML routes
│   ├── auth/                   # Session auth, middleware, role guards
│   ├── scheduler/              # APScheduler (appointment reminders)
│   ├── i18n/                   # Server-side message keys (future)
│   ├── templating.py           # Jinja2 environment + globals
│   └── utils/                  # Shared exceptions, helpers
├── templates/                  # Jinja2 HTML
│   ├── layouts/                # base, public, auth, dashboard shells
│   ├── pages/                  # Route-specific pages
│   ├── sections/landing/       # Landing page partials
│   ├── components/             # navbar, footer, language switcher
│   └── macros/                 # Reusable Jinja macros
├── static/
│   ├── css/                    # Design system (variables → components → pages)
│   └── js/
│       ├── core/               # app bootstrap, modal, toast, navbar
│       ├── i18n/               # Client-side localization (en / sw)
│       ├── pages/              # Page-specific modules
│       ├── modules/            # Shared UI modules (payment simulation)
│       └── utils/              # api.js, scroll-reveal, carousel
├── scripts/                    # seed.py, test_rbac.py, locale generator
├── alembic/                    # Database migrations
├── docs/                       # mysql_schema.sql, this file
├── data/                       # SQLite file (gitignored)
├── cursor/project_rules.md     # Design & coding constitution
├── requirements.txt
└── README.md
```

## Request flow

```
Browser
  → SessionMiddleware / AuthMiddleware / UserContextMiddleware
  → HTML routes (app/routes/)  OR  API routes (app/api/v1/)
  → Service layer (app/services/)
  → SQLAlchemy models → SQLite
```

## Role-based access

| Role    | Web dashboard              | API prefix                    |
|---------|----------------------------|-------------------------------|
| Patient | `/patient/dashboard`       | `/api/v1/patient/...`         |
| Doctor  | `/doctor/dashboard`        | `/api/v1/doctor/...`          |
| Admin   | `/admin/dashboard`         | `/api/v1/admin/...`           |

Cross-role access redirects to the user's own dashboard (HTML) or returns `403` (API).

Generic redirect: `GET /dashboard` → role-appropriate home.

## Frontend architecture

- **Vanilla ES modules** - no React/Vue
- **Design system** - `static/css/variables.css` + component CSS + page CSS
- **i18n** - `static/js/i18n/` with `en.json` / `sw.json`, `data-i18n` attributes, `localStorage`
- **Animations** - `scroll-reveal.js` (Intersection Observer, fade-up, stagger)
- **API client** - `static/js/utils/api.js` → `/api/v1/*`

## Key services

| Service                    | Responsibility                          |
|---------------------------|-----------------------------------------|
| `auth_service`            | Login, register, password reset         |
| `appointment_service`     | Slots, booking, duplicate prevention    |
| `payment_service`         | Simulated mobile money checkout         |
| `reminder_service`        | Pre-appointment notifications           |
| `patient_dashboard_service` | Patient dashboard aggregation         |
| `doctor_dashboard_service`  | Doctor practice management            |
| `admin_dashboard_service`   | Platform admin & analytics            |
| `doctor_service`          | Public doctor directory                 |
| `landing_service`         | Landing page mock/static content        |

## Database

- **Development:** SQLite (`data/medcare.db`)
- **Production-ready:** `docs/mysql_schema.sql` (MySQL 8.0+, utf8mb4)
- **Migrations:** Alembic (`alembic/versions/`)

## Demo accounts (after `python scripts/seed.py`)

| Role    | Email                    | Password        |
|---------|--------------------------|-----------------|
| Admin   | admin@medcare.com        | Admin@123456    |
| Doctor  | s.okello@medcare.com     | Doctor@123456   |
| Patient | amina.hassan@email.com   | Patient@123456  |

## Quality checks

```bash
python scripts/test_rbac.py    # Role isolation smoke test
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

See [`cursor/project_rules.md`](../cursor/project_rules.md) for UI/UX standards.
