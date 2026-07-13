"""Web (HTML) routes package."""

from app.routes.auth import auth_router
from app.routes.dashboard import dashboard_router
from app.routes.web import web_router

__all__ = ["web_router", "auth_router", "dashboard_router"]
