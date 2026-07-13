"""API authentication dependencies - JSON errors, not redirects."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.session import get_session_user_id, logout_user
from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.services.auth_service import get_user_by_id


def get_api_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    user_id = get_session_user_id(request)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = get_user_by_id(db, user_id)
    if not user:
        logout_user(request)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    if not user.is_active:
        logout_user(request)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated",
        )
    return user


def require_api_patient(
    user: User = Depends(get_api_user),
) -> User:
    if user.role != UserRole.PATIENT.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Patients only")
    return user


def require_api_doctor(
    user: User = Depends(get_api_user),
) -> User:
    if user.role != UserRole.DOCTOR.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Doctors only")
    return user


def require_api_admin(
    user: User = Depends(get_api_user),
) -> User:
    if user.role != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admins only")
    return user
