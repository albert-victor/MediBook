"""Public doctor application submission."""

from sqlalchemy.orm import Session

from app.schemas.admin_dashboard import CreateDoctorRequest
from app.schemas.doctor_application import DoctorApplicationForm
from app.services.admin_dashboard_service import create_doctor


def submit_doctor_application(db: Session, form: DoctorApplicationForm):
    """Create an unverified doctor profile pending admin review."""
    payload = CreateDoctorRequest(
        first_name=form.first_name,
        last_name=form.last_name,
        email=form.email,
        phone=form.phone,
        password=form.password,
        specialization_id=form.specialization_id,
        license_number=form.license_number,
        hospital_name=form.hospital_name,
        consultation_fee=form.consultation_fee,
        experience_years=form.experience_years,
        qualification=form.qualification,
        is_verified=False,
        is_accepting_patients=False,
    )
    return create_doctor(db, payload)
