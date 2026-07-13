"""Server-rendered HTML page routes."""

from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_optional
from app.auth.session import set_flash
from app.database import get_db
from app.schemas.doctor_application import DoctorApplicationForm
from app.services.admin_dashboard_service import list_specializations
from app.services.auth_service import get_post_login_redirect
from app.services.content_service import (
    get_careers_content,
    get_partners_content,
    get_privacy_content,
    get_terms_content,
)
from app.services.doctor_application_service import submit_doctor_application
from app.services.landing_service import (
    get_available_today_page_context,
    get_faq_page_context,
    get_footer_data,
    get_landing_context,
    get_search_data,
    get_services,
)
from app.templating import templates
from app.utils.exceptions import ConflictError

web_router = APIRouter(tags=["Web"])


def _validation_errors(exc: ValidationError) -> dict[str, str]:
    errors: dict[str, str] = {}
    for err in exc.errors():
        loc = err.get("loc", ())
        field = str(loc[-1]) if loc else "_form"
        if field == "value" and len(loc) > 1:
            field = str(loc[-2])
        if field not in errors:
            errors[field] = err["msg"]
    return errors


async def _parse_form(request: Request) -> dict[str, Any]:
    form = await request.form()
    data = dict(form)
    data["terms_accepted"] = "terms_accepted" in form
    if data.get("specialization_id"):
        try:
            data["specialization_id"] = int(data["specialization_id"])
        except (TypeError, ValueError):
            pass
    if data.get("experience_years") not in (None, ""):
        try:
            data["experience_years"] = int(data["experience_years"])
        except (TypeError, ValueError):
            pass
    if data.get("consultation_fee") not in (None, ""):
        try:
            data["consultation_fee"] = float(data["consultation_fee"])
        except (TypeError, ValueError):
            pass
    return data


def _careers_context(
    request: Request,
    db: Session,
    *,
    errors: dict[str, str] | None = None,
    form_values: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "request": request,
        "page_title": "Join as a Doctor - mediBook",
        "page_description": (
            "Apply to join mediBook as a verified doctor. Submit your credentials "
            "for admin review and start accepting patients once approved."
        ),
        "footer": get_footer_data(),
        "careers": get_careers_content(),
        "specializations": list_specializations(db),
        "errors": errors or {},
        "form_values": form_values or {},
    }


@web_router.get("/")
async def landing_page(request: Request, db=Depends(get_db)):
    """Public landing page — authenticated users go straight to their dashboard."""
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url=get_post_login_redirect(user), status_code=303)

    context = get_landing_context()
    return templates.TemplateResponse(
        request=request,
        name="pages/landing.html",
        context={
            "request": request,
            "page_title": "mediBook - Book Doctors & Manage Appointments",
            "page_description": (
                "Find verified doctors, book appointments instantly, "
                "and receive smart reminders. Modern healthcare scheduling."
            ),
            **context,
        },
    )


@web_router.get("/services")
async def services_page(request: Request):
    """All medical services - detailed catalogue page."""
    return templates.TemplateResponse(
        request=request,
        name="pages/services.html",
        context={
            "request": request,
            "page_title": "Medical Services - mediBook",
            "page_description": "Explore every medical service available through mediBook partner hospitals.",
            "services": get_services(),
            "search": get_search_data(),
            "footer": get_footer_data(),
        },
    )


@web_router.get("/doctors/available-today")
async def available_today_page(request: Request):
    """Doctors with live same-day availability."""
    page_context = get_available_today_page_context()
    return templates.TemplateResponse(
        request=request,
        name="pages/available_today.html",
        context={
            "request": request,
            "page_title": "Doctors Available Today - mediBook",
            "page_description": "Browse verified doctors with real-time slots available today.",
            **page_context,
        },
    )


@web_router.get("/doctors")
async def doctors_directory(request: Request):
    """Full doctor directory with search and filters."""
    return templates.TemplateResponse(
        request=request,
        name="pages/doctors/index.html",
        context={
            "request": request,
            "page_title": "Find a Doctor - mediBook",
            "page_description": "Browse verified specialists, compare fees, and book appointments instantly.",
            "search": get_search_data(),
            "footer": get_footer_data(),
        },
    )


@web_router.get("/appointments/book")
async def book_appointment_page(request: Request):
    """Multi-step appointment booking wizard."""
    return templates.TemplateResponse(
        request=request,
        name="pages/appointments/book.html",
        context={
            "request": request,
            "page_title": "Book Appointment - mediBook",
            "page_description": "Select a doctor, choose an available time slot, and confirm your visit.",
            "footer": get_footer_data(),
        },
    )


@web_router.get("/appointments/payment/{appointment_id}")
async def payment_page(request: Request, appointment_id: int):
    """Simulated mobile money payment for a booked appointment."""
    return templates.TemplateResponse(
        request=request,
        name="pages/appointments/payment.html",
        context={
            "request": request,
            "page_title": "Complete Payment - mediBook",
            "page_description": "Secure payment for your medical appointment.",
            "appointment_id": appointment_id,
            "footer": get_footer_data(),
        },
    )


@web_router.get("/appointments/confirmation/{appointment_id}")
async def confirmation_page(request: Request, appointment_id: int):
    """Appointment confirmation after successful payment."""
    return templates.TemplateResponse(
        request=request,
        name="pages/appointments/confirmation.html",
        context={
            "request": request,
            "page_title": "Appointment Confirmed - mediBook",
            "page_description": "Your appointment has been confirmed successfully.",
            "appointment_id": appointment_id,
            "footer": get_footer_data(),
        },
    )


@web_router.get("/faq")
async def faq_page(request: Request):
    """Frequently asked questions."""
    page_context = get_faq_page_context()
    return templates.TemplateResponse(
        request=request,
        name="pages/faq.html",
        context={
            "request": request,
            "page_title": "FAQs - mediBook",
            "page_description": (
                "Answers to common questions about booking, payments, "
                "reminders, and managing your care on mediBook."
            ),
            **page_context,
        },
    )


@web_router.get("/help")
async def help_page(request: Request):
    """Patient help centre."""
    return templates.TemplateResponse(
        request=request,
        name="pages/help.html",
        context={
            "request": request,
            "page_title": "Help Centre - mediBook",
            "page_description": "Get help with booking, payments, and appointment reminders.",
            "footer": get_footer_data(),
        },
    )


@web_router.get("/privacy")
async def privacy_page(request: Request):
    """Privacy policy."""
    content = get_privacy_content()
    return templates.TemplateResponse(
        request=request,
        name="pages/legal/privacy.html",
        context={
            "request": request,
            "page_title": "Privacy Policy - mediBook",
            "page_description": "How mediBook collects, uses, and protects your personal information.",
            "footer": get_footer_data(),
            "legal": content,
        },
    )


@web_router.get("/terms")
async def terms_page(request: Request):
    """Terms of service."""
    content = get_terms_content()
    return templates.TemplateResponse(
        request=request,
        name="pages/legal/terms.html",
        context={
            "request": request,
            "page_title": "Terms of Service - mediBook",
            "page_description": "Terms and conditions for using the mediBook healthcare scheduling platform.",
            "footer": get_footer_data(),
            "legal": content,
        },
    )


@web_router.get("/partners")
async def partners_page(request: Request):
    """Partner hospitals directory."""
    content = get_partners_content()
    return templates.TemplateResponse(
        request=request,
        name="pages/partners.html",
        context={
            "request": request,
            "page_title": "Partner Hospitals - mediBook",
            "page_description": "Hospitals and clinics connected to mediBook across Tanzania.",
            "footer": get_footer_data(),
            "partners": content,
        },
    )


@web_router.get("/careers")
async def careers_page(request: Request, db: Session = Depends(get_db)):
    """Doctor application page."""
    return templates.TemplateResponse(
        request=request,
        name="pages/careers.html",
        context=_careers_context(request, db),
    )


@web_router.post("/careers")
async def careers_submit(request: Request, db: Session = Depends(get_db)):
    """Submit a doctor application for admin verification."""
    raw = await _parse_form(request)

    try:
        form = DoctorApplicationForm(
            **{k: v for k, v in raw.items() if k in DoctorApplicationForm.model_fields}
        )
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="pages/careers.html",
            context=_careers_context(request, db, errors=_validation_errors(exc), form_values=raw),
            status_code=422,
        )

    try:
        submit_doctor_application(db, form)
    except ConflictError as exc:
        field = "email" if "email" in exc.message.lower() else "license_number"
        return templates.TemplateResponse(
            request=request,
            name="pages/careers.html",
            context=_careers_context(
                request,
                db,
                errors={field: exc.message},
                form_values={k: v for k, v in raw.items() if k != "password" and k != "confirm_password"},
            ),
            status_code=422,
        )

    set_flash(
        request,
        "Application received. Our team will review your credentials and verify your profile before it goes live.",
        category="success",
    )
    return RedirectResponse(url="/careers", status_code=303)


@web_router.get("/doctors/{doctor_id}")
async def doctor_profile_page(request: Request, doctor_id: int):
    """Individual doctor profile page."""
    return templates.TemplateResponse(
        request=request,
        name="pages/doctors/profile.html",
        context={
            "request": request,
            "page_title": "Doctor Profile - mediBook",
            "page_description": "View qualifications, availability, and patient reviews.",
            "doctor_id": doctor_id,
            "footer": get_footer_data(),
        },
    )
