"""Seed medical specializations lookup table."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Specialization

SPECIALIZATIONS = [
    ("General Physician", "general-physician", "bi-heart-pulse", "Primary care and general health consultations."),
    ("Cardiologist", "cardiologist", "bi-heart", "Heart and cardiovascular system specialists."),
    ("Pediatrician", "pediatrician", "bi-emoji-smile", "Medical care for infants, children, and adolescents."),
    ("Dermatologist", "dermatologist", "bi-droplet", "Skin, hair, and nail conditions."),
    ("Gynecologist", "gynecologist", "bi-gender-female", "Women's reproductive health and wellness."),
    ("Orthopedic Surgeon", "orthopedic", "bi-person-arms-up", "Bones, joints, and musculoskeletal system."),
    ("Neurologist", "neurologist", "bi-brain", "Brain, spine, and nervous system disorders."),
    ("Dentist", "dentist", "bi-emoji-smile", "Oral health and dental procedures."),
    ("Ophthalmologist", "ophthalmologist", "bi-eye", "Eye care and vision specialists."),
    ("Psychiatrist", "psychiatrist", "bi-emoji-neutral", "Mental health and psychiatric care."),
    ("Urologist", "urologist", "bi-hospital", "Urinary tract and male reproductive health."),
    ("Endocrinologist", "endocrinologist", "bi-activity", "Hormones, diabetes, and metabolic disorders."),
]


def seed_specializations(db: Session) -> int:
    created = 0
    for name, slug, icon, description in SPECIALIZATIONS:
        if db.scalar(select(Specialization).where(Specialization.slug == slug)):
            continue
        db.add(
            Specialization(
                name=name,
                slug=slug,
                icon=icon,
                description=description,
                is_active=True,
            )
        )
        created += 1
    db.commit()
    return created
