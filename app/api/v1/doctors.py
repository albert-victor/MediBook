"""Public doctor directory API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.doctor import DoctorDirectoryMeta, DoctorListItem, DoctorProfile
from app.services import doctor_service as svc

doctors_api_router = APIRouter(prefix="/doctors", tags=["Doctors"])


@doctors_api_router.get("", response_model=list[DoctorListItem])
async def list_doctors(
    q: str | None = Query(None, description="Search by name, specialty, or hospital"),
    specialization: str | None = Query(None, alias="specialty"),
    availability: str | None = Query(None, pattern="^(today|week|any)?$"),
    gender: str | None = Query(None, pattern="^(male|female)?$"),
    fee_min: float | None = Query(None, ge=0),
    fee_max: float | None = Query(None, ge=0),
    db: Session = Depends(get_db),
):
    return svc.list_doctors(
        db,
        q=q,
        specialization=specialization,
        availability=availability if availability != "any" else None,
        gender=gender,
        fee_min=fee_min,
        fee_max=fee_max,
    )


@doctors_api_router.get("/meta", response_model=DoctorDirectoryMeta)
async def directory_meta(db: Session = Depends(get_db)):
    return svc.get_directory_meta(db)


@doctors_api_router.get("/{doctor_id}", response_model=DoctorProfile)
async def doctor_profile(doctor_id: int, db: Session = Depends(get_db)):
    profile = svc.get_doctor_profile(db, doctor_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")
    return profile
