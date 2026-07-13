"""API v1 router aggregation."""

from fastapi import APIRouter

from app.api.v1.admin import admin_api_router
from app.api.v1.appointments import appointments_api_router
from app.api.v1.doctor import doctor_api_router
from app.api.v1.doctors import doctors_api_router
from app.api.v1.patient import patient_api_router
from app.api.v1.payments import payments_api_router
from app.config import get_settings

settings = get_settings()

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(doctors_api_router)
api_v1_router.include_router(patient_api_router)
api_v1_router.include_router(doctor_api_router)
api_v1_router.include_router(admin_api_router)
api_v1_router.include_router(appointments_api_router)
api_v1_router.include_router(payments_api_router)


@api_v1_router.get("/health", tags=["Health"])
async def health_check():
    """Return API health status."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }
