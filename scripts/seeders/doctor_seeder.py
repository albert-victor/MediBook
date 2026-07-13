"""Seed doctor accounts and doctor profiles."""

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.models import Doctor, Specialization, User
from app.models.enums import UserRole

# (first, last, email, phone, spec_slug, hospital, license, fee, years)
DOCTORS = [
    ("Sarah", "Okello", "s.okello@medcare.com", "+255711000001", "cardiologist", "City Medical Centre", "MD-TZ-001", 85000, 15),
    ("James", "Mwangi", "j.mwangi@medcare.com", "+255711000002", "general-physician", "Kilimanjaro Clinic", "MD-TZ-002", 45000, 12),
    ("Fatuma", "Saidi", "f.saidi@medcare.com", "+255711000003", "pediatrician", "Hope Children's Hospital", "MD-TZ-003", 55000, 18),
    ("Peter", "Kimaro", "p.kimaro@medcare.com", "+255711000004", "orthopedic", "Orthocare Institute", "MD-TZ-004", 95000, 20),
    ("Grace", "Mushi", "g.mushi@medcare.com", "+255711000005", "dermatologist", "Skin Health Clinic", "MD-TZ-005", 60000, 10),
    ("David", "Lyimo", "d.lyimo@medcare.com", "+255711000006", "neurologist", "NeuroCare Hospital", "MD-TZ-006", 120000, 22),
    ("Neema", "Juma", "n.juma@medcare.com", "+255711000007", "gynecologist", "Women's Wellness Centre", "MD-TZ-007", 70000, 14),
    ("Robert", "Msigwa", "r.msigwa@medcare.com", "+255711000008", "dentist", "Smile Dental Studio", "MD-TZ-008", 40000, 8),
    ("Aisha", "Hassan", "a.hassan@medcare.com", "+255711000009", "ophthalmologist", "Vision Plus Eye Centre", "MD-TZ-009", 75000, 16),
    ("Emmanuel", "Tenga", "e.tenga@medcare.com", "+255711000010", "psychiatrist", "MindCare Clinic", "MD-TZ-010", 90000, 11),
    ("John", "Bakari", "j.bakari@medcare.com", "+255711000011", "urologist", "UroHealth Clinic", "MD-TZ-011", 80000, 13),
    ("Lucy", "Mwanga", "l.mwanga@medcare.com", "+255711000012", "endocrinologist", "Metabolic Care Centre", "MD-TZ-012", 85000, 12),
    ("Samuel", "Rwezaula", "s.rwezaula@medcare.com", "+255711000013", "general-physician", "Muhimbili Partner Clinic", "MD-TZ-013", 50000, 9),
    ("Catherine", "Mollel", "c.mollel@medcare.com", "+255711000014", "cardiologist", "HeartLink Hospital", "MD-TZ-014", 90000, 17),
    ("Hassan", "Omary", "h.omary@medcare.com", "+255711000015", "pediatrician", "Little Stars Paediatrics", "MD-TZ-015", 58000, 11),
    ("Judith", "Mwakyusa", "j.mwakyusa@medcare.com", "+255711000016", "dermatologist", "Derma Plus Clinic", "MD-TZ-016", 62000, 9),
    ("Frank", "Ngowi", "f.ngowi@medcare.com", "+255711000017", "gynecologist", "Amana Women's Hospital", "MD-TZ-017", 72000, 15),
    ("Mary", "Kilonzo", "m.kilonzo@medcare.com", "+255711000018", "orthopedic", "Bone & Joint Centre", "MD-TZ-018", 98000, 19),
    ("Paul", "Mcharo", "p.mcharo@medcare.com", "+255711000019", "neurologist", "Brain & Spine Institute", "MD-TZ-019", 115000, 21),
    ("Salma", "Rajab", "s.rajab@medcare.com", "+255711000020", "dentist", "Pearl Dental Care", "MD-TZ-020", 42000, 7),
    ("Vincent", "Malima", "v.malima@medcare.com", "+255711000021", "ophthalmologist", "Clear Vision Hospital", "MD-TZ-021", 78000, 14),
    ("Zainab", "Ali", "z.ali@medcare.com", "+255711000022", "psychiatrist", "Serenity Mental Health", "MD-TZ-022", 88000, 10),
    ("Thomas", "Mwambene", "t.mwambene@medcare.com", "+255711000023", "general-physician", "Arusha Community Clinic", "MD-TZ-023", 48000, 16),
    ("Rachel", "Kimathi", "r.kimathi@medcare.com", "+255711000024", "cardiologist", "Coastal Cardiac Centre", "MD-TZ-024", 92000, 13),
    ("Issa", "Mbena", "i.mbena@medcare.com", "+255711000025", "pediatrician", "Mwanza Kids Care", "MD-TZ-025", 52000, 8),
]

DEFAULT_PASSWORD = "Doctor@123456"


def seed_doctors(db: Session) -> int:
    created = 0
    for first, last, email, phone, spec_slug, hospital, license_no, fee, years in DOCTORS:
        spec = db.scalar(select(Specialization).where(Specialization.slug == spec_slug))
        if not spec:
            continue

        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                first_name=first,
                last_name=last,
                email=email,
                phone=phone,
                password_hash=hash_password(DEFAULT_PASSWORD),
                role=UserRole.DOCTOR.value,
                is_active=True,
            )
            db.add(user)
            db.flush()
            created += 1

        if not user.doctor_profile:
            db.add(
                Doctor(
                    user_id=user.id,
                    specialization_id=spec.id,
                    license_number=license_no,
                    hospital_name=hospital,
                    consultation_fee=Decimal(str(fee)),
                    experience_years=years,
                    is_verified=True,
                    is_accepting_patients=True,
                )
            )

    db.commit()
    return created
