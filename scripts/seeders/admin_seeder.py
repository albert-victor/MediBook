"""Seed admin accounts and admin profiles."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models import Admin, User
from app.models.enums import UserRole

ADMINS = [
    {
        "first_name": "System",
        "last_name": "Administrator",
        "email": "admin@medcare.com",
        "phone": "+255700000001",
        "password": "Admin@123456",
        "department": "IT",
        "job_title": "System Administrator",
    },
    {
        "first_name": "Operations",
        "last_name": "Manager",
        "email": "operations@medcare.com",
        "phone": "+255700000002",
        "password": "OpsAdmin@123456",
        "department": "Operations",
        "job_title": "Operations Manager",
    },
]


def seed_admins(db: Session) -> int:
    created = 0
    for data in ADMINS:
        user = db.scalar(select(User).where(User.email == data["email"]))
        if not user:
            user = User(
                first_name=data["first_name"],
                last_name=data["last_name"],
                email=data["email"],
                phone=data["phone"],
                password_hash=hash_password(data["password"]),
                role=UserRole.ADMIN.value,
                is_active=True,
            )
            db.add(user)
            db.flush()
            created += 1

        if not user.admin_profile:
            db.add(
                Admin(
                    user_id=user.id,
                    department=data["department"],
                    job_title=data["job_title"],
                )
            )

    db.commit()
    return created
