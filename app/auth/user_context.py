"""User context middleware - loads current user into request.state."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.auth.session import get_session_user_id, logout_user, pop_flash, SESSION_ROLE_KEY
from app.database import SessionLocal
from app.services.auth_service import get_user_by_id


class UserContextMiddleware(BaseHTTPMiddleware):
    """Attach current user and flash messages to every request."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.user = None
        request.state.flash = pop_flash(request)

        user_id = get_session_user_id(request)
        if user_id:
            db = SessionLocal()
            try:
                user = get_user_by_id(db, user_id)
                if user and not user.is_active:
                    logout_user(request)
                    user = None
                request.state.user = user
                if user:
                    request.session[SESSION_ROLE_KEY] = user.role
            finally:
                db.close()

        return await call_next(request)
