"""Seed demo patient accounts for development."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models import User
from app.models.enums import UserRole

PATIENTS = [
    ("Amina", "Hassan", "amina.hassan@email.com", "+255712000001"),
    ("Michael", "Ndege", "michael.ndege@email.com", "+255712000002"),
    ("Halima", "Yusuf", "halima.yusuf@email.com", "+255712000003"),
    ("Joseph", "Mollel", "joseph.mollel@email.com", "+255712000004"),
    ("Elizabeth", "Mwakasege", "elizabeth.m@email.com", "+255712000005"),
    ("Daniel", "Kessy", "daniel.kessy@email.com", "+255712000006"),
    ("Rehema", "Swai", "rehema.swai@email.com", "+255712000007"),
    ("Patrick", "Shayo", "patrick.shayo@email.com", "+255712000008"),
    ("Christina", "Massawe", "christina.m@email.com", "+255712000009"),
    ("George", "Marwa", "george.marwa@email.com", "+255712000010"),
    ("Susan", "Temba", "susan.temba@email.com", "+255712000011"),
    ("Brian", "Mrosso", "brian.mrosso@email.com", "+255712000012"),
    ("Faith", "Mboya", "faith.mboya@email.com", "+255712000013"),
    ("Kelvin", "Mrosso", "kelvin.mrosso@email.com", "+255712000014"),
    ("Lucia", "Tarimo", "lucia.tarimo@email.com", "+255712000015"),
    ("Oscar", "Mrema", "oscar.mrema@email.com", "+255712000016"),
    ("Prisca", "Lyatuu", "prisca.lyatuu@email.com", "+255712000017"),
    ("Simon", "Mkumbo", "simon.mkumbo@email.com", "+255712000018"),
    ("Teresa", "Ngowi", "teresa.ngowi@email.com", "+255712000019"),
    ("Victor", "Macha", "victor.macha@email.com", "+255712000020"),
    ("Winnie", "Kavishe", "winnie.kavishe@email.com", "+255712000021"),
    ("Yusuf", "Hemed", "yusuf.hemed@email.com", "+255712000022"),
    ("Zawadi", "Mfinanga", "zawadi.mfinanga@email.com", "+255712000023"),
    ("Abel", "Kwayu", "abel.kwayu@email.com", "+255712000024"),
    ("Beatrice", "Shirima", "beatrice.shirima@email.com", "+255712000025"),
]

DEFAULT_PASSWORD = "Patient@123456"


def seed_patients(db: Session) -> int:
    created = 0
    for first, last, email, phone in PATIENTS:
        if db.scalar(select(User).where(User.email == email)):
            continue
        db.add(
            User(
                first_name=first,
                last_name=last,
                email=email,
                phone=phone,
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=UserRole.PATIENT.value,
                is_active=True,
            )
        )
        created += 1
    db.commit()
    return created
