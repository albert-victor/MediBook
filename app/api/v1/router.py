"""API v1 router aggregation."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.api.v1.admin import admin_api_router
from app.api.v1.appointments import appointments_api_router
from app.api.v1.doctor import doctor_api_router
from app.api.v1.doctors import doctors_api_router
from app.api.v1.patient import patient_api_router
from app.api.v1.payments import payments_api_router
from app.auth.api_dependencies import get_api_user
from app.config import get_settings
from app.database import get_db
from app.models import User

settings = get_settings()

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(doctors_api_router)
api_v1_router.include_router(patient_api_router)
api_v1_router.include_router(doctor_api_router)
api_v1_router.include_router(admin_api_router)
api_v1_router.include_router(appointments_api_router)
api_v1_router.include_router(payments_api_router)


class LanguageUpdate(BaseModel):
    language: str = Field(..., min_length=2, max_length=5)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        code = value.strip().lower()
        if code not in {"en", "sw"}:
            raise ValueError("language must be 'en' or 'sw'")
        return code


@api_v1_router.get("/health", tags=["Health"])
async def health_check():
    """Return API health status."""
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@api_v1_router.patch("/me/language", tags=["Account"])
async def update_my_language(
    payload: LanguageUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_api_user),
):
    """Persist UI language so SMS reminders match the patient's choice."""
    user.preferred_language = payload.language
    db.commit()
    return {"language": user.preferred_language}

