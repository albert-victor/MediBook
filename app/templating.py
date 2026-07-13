"""Jinja2 template engine configuration."""

from datetime import datetime

from fastapi.templating import Jinja2Templates

from app.config import get_settings

settings = get_settings()

templates = Jinja2Templates(directory=str(settings.templates_dir))


def _current_user(request):
    return getattr(request.state, "user", None)


def _flash(request):
    return getattr(request.state, "flash", None)


def _dashboard_url(user) -> str:
    if not user:
        return "/"
    if user.is_admin:
        return "/admin/dashboard"
    if user.is_doctor:
        return "/doctor/dashboard"
    return "/patient/dashboard"


templates.env.globals["get_current_user"] = _current_user
templates.env.globals["get_flash"] = _flash
templates.env.globals["dashboard_url"] = _dashboard_url
templates.env.globals["now"] = datetime.now
templates.env.globals["static_v"] = settings.static_asset_version
templates.env.globals["brand_name"] = settings.brand_name
