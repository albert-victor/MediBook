"""Role-specific dashboard HTML routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_optional, role_guard
from app.database import get_db
from app.models import User
from app.models.enums import UserRole
from app.services.auth_service import get_post_login_redirect
from app.templating import templates

dashboard_router = APIRouter(tags=["Dashboard"])


def _dashboard_context(request: Request, user: User, title: str) -> dict:
    return {
        "request": request,
        "current_user": user,
        "page_title": title,
    }


@dashboard_router.get("/dashboard")
async def role_dashboard_redirect(
    request: Request,
    db: Session = Depends(get_db),
):
    """Send authenticated users to their role-appropriate dashboard."""
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return RedirectResponse(url=get_post_login_redirect(user), status_code=303)


@dashboard_router.get("/patient/dashboard", response_class=HTMLResponse)
async def patient_dashboard(request: Request, db: Session = Depends(get_db)):
    user, redirect = role_guard(get_current_user_optional(request, db), UserRole.PATIENT)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard/patient/index.html",
        context=_dashboard_context(request, user, "My Health - mediBook"),
    )


@dashboard_router.get("/doctor/dashboard", response_class=HTMLResponse)
async def doctor_dashboard(request: Request, db: Session = Depends(get_db)):
    user, redirect = role_guard(get_current_user_optional(request, db), UserRole.DOCTOR)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard/doctor/index.html",
        context=_dashboard_context(request, user, "Doctor Dashboard - mediBook"),
    )


@dashboard_router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user, redirect = role_guard(get_current_user_optional(request, db), UserRole.ADMIN)
    if redirect:
        return redirect
    return templates.TemplateResponse(
        request=request,
        name="pages/dashboard/admin/index.html",
        context=_dashboard_context(request, user, "Admin Dashboard - mediBook"),
    )
