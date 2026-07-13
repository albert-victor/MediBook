"""Doctor dashboard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.api_dependencies import require_api_doctor
from app.database import get_db
from app.models import User
from app.schemas.doctor_dashboard import (
    CancelAppointmentRequest,
    DoctorActivityItem,
    DoctorAppointmentItem,
    DoctorCalendarDay,
    DoctorDashboardOverview,
    DoctorPatientBrief,
    DoctorPatientDetail,
)
from app.services import doctor_dashboard_service as svc
from app.utils.exceptions import AppException

doctor_api_router = APIRouter(prefix="/doctor", tags=["Doctor Dashboard"])


@doctor_api_router.get("/dashboard/overview", response_model=DoctorDashboardOverview)
async def dashboard_overview(
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    return svc.get_overview(db, doctor)


@doctor_api_router.get("/dashboard/appointments/today", response_model=list[DoctorAppointmentItem])
async def today_appointments(
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    return svc.get_today_appointments(db, doctor)


@doctor_api_router.get("/dashboard/appointments", response_model=list[DoctorAppointmentItem])
async def list_appointments(
    q: str | None = Query(None, description="Search patient name, email, or phone"),
    date: str | None = Query(None, description="Filter by date YYYY-MM-DD"),
    status: str | None = Query(
        None,
        pattern="^(today|upcoming|completed|cancelled|pending)?$",
    ),
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.list_appointments(db, doctor, q=q, date_filter=date, status_filter=status)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@doctor_api_router.get("/dashboard/appointments/{appointment_id}", response_model=DoctorAppointmentItem)
async def appointment_detail(
    appointment_id: int,
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.get_appointment(db, doctor, appointment_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@doctor_api_router.patch("/dashboard/appointments/{appointment_id}/approve", response_model=DoctorAppointmentItem)
async def approve_appointment(
    appointment_id: int,
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.approve_appointment(db, doctor, appointment_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@doctor_api_router.patch("/dashboard/appointments/{appointment_id}/cancel", response_model=DoctorAppointmentItem)
async def cancel_appointment(
    appointment_id: int,
    payload: CancelAppointmentRequest,
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.cancel_appointment(db, doctor, appointment_id, payload.reason)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@doctor_api_router.patch("/dashboard/appointments/{appointment_id}/complete", response_model=DoctorAppointmentItem)
async def complete_appointment(
    appointment_id: int,
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.complete_appointment(db, doctor, appointment_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@doctor_api_router.get("/dashboard/patients", response_model=list[DoctorPatientBrief])
async def patient_list(
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    return svc.list_patients(db, doctor)


@doctor_api_router.get("/dashboard/patients/{patient_id}", response_model=DoctorPatientDetail)
async def patient_detail(
    patient_id: int,
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.get_patient_detail(db, doctor, patient_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@doctor_api_router.get("/dashboard/activity", response_model=list[DoctorActivityItem])
async def recent_activity(
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    return svc.get_recent_activity(db, doctor)


@doctor_api_router.get("/dashboard/calendar", response_model=list[DoctorCalendarDay])
async def appointment_calendar(
    month: str | None = Query(None, description="YYYY-MM"),
    doctor: User = Depends(require_api_doctor),
    db: Session = Depends(get_db),
):
    try:
        return svc.get_calendar(db, doctor, month)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
