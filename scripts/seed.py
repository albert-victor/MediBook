"""Run all database seeders."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import (  # noqa: F401 - register metadata
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
from scripts.seeders.admin_seeder import seed_admins
from scripts.seeders.availability_seeder import seed_availability
from scripts.seeders.dashboard_seeder import seed_dashboard_data
from scripts.seeders.doctor_profile_seeder import seed_doctor_profiles
from scripts.seeders.doctor_seeder import seed_doctors
from scripts.seeders.patient_seeder import seed_patients
from scripts.seeders.specialization_seeder import seed_specializations


def main() -> None:
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        specs = seed_specializations(db)
        admins = seed_admins(db)
        doctors = seed_doctors(db)
        profiles = seed_doctor_profiles(db)
        patients = seed_patients(db)
        availability = seed_availability(db)
        dashboard = seed_dashboard_data(db)
    finally:
        db.close()

    print("Seed complete:")
    print(f"  Specializations:  {specs}")
    print(f"  Admins created:   {admins}")
    print(f"  Doctors created:  {doctors}")
    print(f"  Doctor profiles:  {profiles}")
    print(f"  Patients created: {patients}")
    print(f"  Availability slots: {availability}")
    print(f"  Dashboard data:   {dashboard}")
    print()
    print("Admin login:")
    print("  admin@medcare.com / Admin@123456")
    print("  operations@medcare.com / OpsAdmin@123456")
    print("Doctor login (all seeded doctors):")
    print("  *@medcare.com / Doctor@123456")
    print("Patient login (all seeded patients):")
    print("  *@email.com / Patient@123456")


if __name__ == "__main__":
    main()
