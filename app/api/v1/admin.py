"""Admin dashboard API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.api_dependencies import require_api_admin
from app.database import get_db
from app.models import User
from app.schemas.admin_dashboard import (
    AdminAppointmentItem,
    AdminDashboardOverview,
    AdminDoctorItem,
    AdminNotificationItem,
    AdminPatientItem,
    AdminPaymentItem,
    AdminReportSummary,
    AdminSettingsView,
    CreateDoctorRequest,
    SpecializationOption,
    UpdateDoctorRequest,
)
from app.services import admin_dashboard_service as svc
from app.utils.exceptions import AppException

admin_api_router = APIRouter(prefix="/admin", tags=["Admin Dashboard"])


@admin_api_router.get("/dashboard/overview", response_model=AdminDashboardOverview)
async def dashboard_overview(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.get_overview(db, admin)


@admin_api_router.get("/dashboard/doctors", response_model=list[AdminDoctorItem])
async def list_doctors(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.list_doctors(db)


@admin_api_router.post("/dashboard/doctors", response_model=AdminDoctorItem, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    payload: CreateDoctorRequest,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    try:
        return svc.create_doctor(db, payload)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@admin_api_router.patch("/dashboard/doctors/{doctor_id}", response_model=AdminDoctorItem)
async def update_doctor(
    doctor_id: int,
    payload: UpdateDoctorRequest,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    try:
        return svc.update_doctor(db, doctor_id, payload)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@admin_api_router.patch("/dashboard/doctors/{doctor_id}/deactivate", response_model=AdminDoctorItem)
async def deactivate_doctor(
    doctor_id: int,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    try:
        return svc.deactivate_doctor(db, doctor_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@admin_api_router.delete("/dashboard/doctors/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_doctor(
    doctor_id: int,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    try:
        svc.delete_doctor(db, doctor_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@admin_api_router.get("/dashboard/patients", response_model=list[AdminPatientItem])
async def list_patients(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.list_patients(db)


@admin_api_router.patch("/dashboard/patients/{patient_id}/deactivate", response_model=AdminPatientItem)
async def deactivate_patient(
    patient_id: int,
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    try:
        return svc.deactivate_patient(db, patient_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@admin_api_router.get("/dashboard/appointments", response_model=list[AdminAppointmentItem])
async def list_appointments(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.list_appointments(db)


@admin_api_router.get("/dashboard/payments", response_model=list[AdminPaymentItem])
async def list_payments(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.list_payments(db)


@admin_api_router.get("/dashboard/notifications", response_model=list[AdminNotificationItem])
async def list_notifications(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.list_notifications(db)


@admin_api_router.get("/dashboard/reports", response_model=AdminReportSummary)
async def report_summary(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.get_report_summary(db)


@admin_api_router.get("/dashboard/settings", response_model=AdminSettingsView)
async def settings_view(
    admin: User = Depends(require_api_admin),
):
    return svc.get_settings_view()


@admin_api_router.get("/dashboard/specializations", response_model=list[SpecializationOption])
async def specializations(
    admin: User = Depends(require_api_admin),
    db: Session = Depends(get_db),
):
    return svc.list_specializations(db)
