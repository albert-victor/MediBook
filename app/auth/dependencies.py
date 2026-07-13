from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.session import get_session_user_id, logout_user
from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.services.auth_service import get_post_login_redirect, get_user_by_id


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    user_id = get_session_user_id(request)
    if not user_id:
        return None
    user = get_user_by_id(db, user_id)
    if not user:
        logout_user(request)
        return None
    if not user.is_active:
        logout_user(request)
        return None
    return user


def role_guard(
    user: User | None,
    *roles: UserRole,
) -> tuple[User | None, RedirectResponse | None]:
    """Return (user, None) when authorized, or (None, redirect) when not."""
    if not user:
        return None, RedirectResponse(url="/login", status_code=303)
    allowed = [r.value for r in roles]
    if user.role not in allowed:
        return None, RedirectResponse(url=get_post_login_redirect(user), status_code=303)
    return user, None


def require_role(*roles: UserRole):
    """Dependency factory - use role_guard in route handlers for HTML redirects."""

    async def dependency(
        request: Request,
        db: Session = Depends(get_db),
    ) -> User:
        user, redirect = role_guard(get_current_user_optional(request, db), *roles)
        if redirect:
            return redirect  # type: ignore[return-value]
        return user  # type: ignore[return-value]

    return dependency


require_admin = require_role(UserRole.ADMIN)
require_patient = require_role(UserRole.PATIENT)
require_doctor = require_role(UserRole.DOCTOR)
