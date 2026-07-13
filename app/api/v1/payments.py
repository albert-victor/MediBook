"""Payment API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.api_dependencies import require_api_patient
from app.database import get_db
from app.models import User
from app.schemas.appointment import (
    ConfirmationContext,
    InitiatePaymentResult,
    PaymentContext,
    PaymentResult,
    ProcessPaymentRequest,
)
from app.services import payment_service as svc
from app.utils.exceptions import AppException

payments_api_router = APIRouter(prefix="/payments", tags=["Payments"])


@payments_api_router.get("/appointment/{appointment_id}", response_model=PaymentContext)
async def payment_context(
    appointment_id: int,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    context = svc.get_payment_context(db, patient.id, appointment_id)
    if not context:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return context


@payments_api_router.get("/appointment/{appointment_id}/confirmation", response_model=ConfirmationContext)
async def confirmation_context(
    appointment_id: int,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    context = svc.get_confirmation_context(db, patient.id, appointment_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Confirmation not available - payment may still be pending",
        )
    return context


@payments_api_router.post("/appointment/{appointment_id}/initiate", response_model=InitiatePaymentResult)
async def initiate_payment(
    appointment_id: int,
    payload: ProcessPaymentRequest,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    try:
        return svc.initiate_payment(db, patient.id, appointment_id, payload)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@payments_api_router.post("/appointment/{appointment_id}/complete", response_model=PaymentResult)
async def complete_payment(
    appointment_id: int,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    try:
        return svc.complete_payment(db, patient.id, appointment_id)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@payments_api_router.post("/appointment/{appointment_id}", response_model=PaymentResult)
async def process_payment(
    appointment_id: int,
    payload: ProcessPaymentRequest,
    db: Session = Depends(get_db),
    patient: User = Depends(require_api_patient),
):
    """Legacy one-shot endpoint - initiates and completes in one call."""
    try:
        return svc.process_payment(db, patient.id, appointment_id, payload)
    except AppException as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
