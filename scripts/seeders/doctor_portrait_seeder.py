"""Assign unique portrait URLs to each doctor from gender image pools."""

from sqlalchemy.orm import Session

from app.utils.doctor_images import assign_doctor_portraits


def seed_doctor_portraits(db: Session) -> dict[str, int]:
    updated = assign_doctor_portraits(db)
    return {"portraits": updated}
