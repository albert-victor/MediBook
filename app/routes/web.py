"""Server-rendered HTML page routes."""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse

from app.auth.dependencies import get_current_user_optional
from app.database import get_db
from app.services.auth_service import get_post_login_redirect
from app.services.landing_service import (
    get_available_today_page_context,
    get_faq_page_context,
    get_footer_data,
    get_landing_context,
    get_search_data,
    get_services,
)
from app.templating import templates

web_router = APIRouter(tags=["Web"])


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
