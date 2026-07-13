"""Appointment booking API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.api_dependencies import require_api_patient
from app.database import get_db
from app.models import User
from app.schemas.appointment import (
    BookingDoctor,
    BookingSlot,
    BookingSummary,
    CreateBookingRequest,
)
from app.services import appointment_service as svc
from app.utils.exceptions import AppException

appointments_api_router = APIRouter(prefix="/appointments", tags=["Appointments"])


@appointments_api_router.get("/doctors", response_model=list[BookingDoctor])
async def list_booking_doctors(
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    return svc.list_booking_doctors(db)


@appointments_api_router.get("/slots", response_model=list[BookingSlot])
async def get_available_slots(
    doctor_id: int = Query(..., ge=1),
    date: str = Query(..., description="ISO date YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _patient: User = Depends(require_api_patient),
):
    try:
        return svc.get_slots_for_date(db, doctor_id, date)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@appointments_api_router.post("", response_model=BookingSummary, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: CreateBookingRequest,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    try:
        return svc.create_booking(db, patient, payload)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@appointments_api_router.get("/{appointment_id}/summary", response_model=BookingSummary)
async def booking_summary(
    appointment_id: int,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    summary = svc.get_booking_summary(db, patient.id, appointment_id)
    if not summary:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return summary
