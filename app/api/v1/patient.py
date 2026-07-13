"""Patient dashboard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.api_dependencies import require_api_patient
from app.database import get_db
from app.models import User
from app.schemas.patient_dashboard import (
    AppointmentItem,
    DashboardOverview,
    DoctorBrief,
    NotificationItem,
    PaymentItem,
)
from app.services import patient_dashboard_service as svc

patient_api_router = APIRouter(prefix="/patient", tags=["Patient Dashboard"])


@patient_api_router.get("/dashboard/overview", response_model=DashboardOverview)
async def dashboard_overview(
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    return svc.get_overview(db, patient)


@patient_api_router.get("/dashboard/appointments", response_model=list[AppointmentItem])
async def appointment_history(
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    return svc.get_appointment_history(db, patient.id)


@patient_api_router.get("/dashboard/payments", response_model=list[PaymentItem])
async def payment_history(
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    return svc.get_payment_history(db, patient.id)


@patient_api_router.get("/dashboard/notifications", response_model=list[NotificationItem])
async def notifications(
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    return svc.get_notifications(db, patient.id)


@patient_api_router.get("/dashboard/doctors/available", response_model=list[DoctorBrief])
async def available_doctors(
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    return svc.get_available_doctors(db)


@patient_api_router.get("/dashboard/doctors/recent", response_model=list[DoctorBrief])
async def recent_doctors(
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    return svc.get_recently_visited_doctors(db, patient.id)


@patient_api_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    patient: User = Depends(require_api_patient),
    db: Session = Depends(get_db),
):
    if not svc.mark_notification_read(db, patient.id, notification_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    return {"ok": True}
