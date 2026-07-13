"""Route protection middleware - session-based."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from app.auth.session import SESSION_ROLE_KEY, SESSION_USER_KEY, set_flash
from app.models.enums import UserRole
from app.services.auth_service import get_dashboard_path_for_role

PROTECTED_PREFIXES = (
    "/patient/",
    "/doctor/",
    "/admin/",
    "/appointments/",
    "/profile/",
)

GUEST_ONLY_PREFIXES = (
    "/login",
    "/register",
    "/forgot-password",
    "/reset-password",
)

AUTHENTICATED_SKIP_PATHS = frozenset({"/"})

PATIENT_ONLY_BOOKING_PATHS = frozenset({"/appointments/book"})
PATIENT_ONLY_BOOKING_PREFIXES = (
    "/appointments/payment/",
    "/appointments/confirmation/",
)


def _is_patient_booking_path(path: str) -> bool:
    if path in PATIENT_ONLY_BOOKING_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PATIENT_ONLY_BOOKING_PREFIXES)


class AuthMiddleware(BaseHTTPMiddleware):
    """Redirect unauthenticated users away from protected routes."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        user_id = request.session.get(SESSION_USER_KEY)

        if not user_id and any(path.startswith(p) for p in PROTECTED_PREFIXES):
            next_url = path
            if request.url.query:
                next_url = f"{path}?{request.url.query}"
            return RedirectResponse(url=f"/login?next={next_url}", status_code=303)

        if user_id:
            role = request.session.get(SESSION_ROLE_KEY, "patient")
            dashboard = get_dashboard_path_for_role(role)

            if path in AUTHENTICATED_SKIP_PATHS:
                return RedirectResponse(url=dashboard, status_code=303)

            if any(path == p or path.startswith(p + "/") for p in GUEST_ONLY_PREFIXES):
                return RedirectResponse(url=dashboard, status_code=303)

            if _is_patient_booking_path(path) and role != UserRole.PATIENT.value:
                set_flash(
                    request,
                    "Appointment booking is only available for patient accounts.",
                    category="warning",
                )
                return RedirectResponse(url=dashboard, status_code=303)

        return await call_next(request)
