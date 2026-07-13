"""Initialize the database schema."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.database import Base, engine
from app.models import (  # noqa: F401 - register all models
    Admin,
    Appointment,
    AppointmentStatusHistory,
    Doctor,
    DoctorAvailability,
    Notification,
    PasswordResetToken,
    Payment,
    Specialization,
    User,
)


def main() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {settings.database_url}")
    print("Tables:", ", ".join(sorted(Base.metadata.tables.keys())))


if __name__ == "__main__":
    main()
