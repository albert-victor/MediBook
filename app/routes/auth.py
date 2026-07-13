"""Authentication page routes."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.auth.session import login_user, logout_user, set_flash
from app.config import get_settings
from app.database import get_db
from app.schemas.auth import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from app.services.auth_service import (
    AuthError,
    authenticate_user,
    create_password_reset,
    get_post_login_redirect,
    resolve_login_redirect,
    get_valid_reset_token,
    register_patient,
    reset_password,
)
from app.templating import templates

logger = logging.getLogger(__name__)
settings = get_settings()

auth_router = APIRouter(tags=["Auth"])


def _form_data(request: Request) -> dict[str, Any]:
    return dict(request.scope.get("_form", {}))


async def _parse_form(request: Request) -> dict[str, str]:
    form = await request.form()
    data = dict(form)
    data["remember_me"] = "remember_me" in form
    data["terms_accepted"] = "terms_accepted" in form
    return data


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


def _auth_context(request: Request, **extra) -> dict[str, Any]:
    return {
        "request": request,
        "current_user": getattr(request.state, "user", None),
        "flash": getattr(request.state, "flash", None),
        "errors": {},
        "form_values": {},
        **extra,
    }


# ── Login ──────────────────────────────────────────────────

@auth_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="pages/auth/login.html",
        context=_auth_context(
            request,
            page_title="Sign In - mediBook",
            next_url=next,
        ),
    )


@auth_router.post("/login")
async def login_submit(request: Request, db: Session = Depends(get_db)):
    raw = await _parse_form(request)
    next_url = raw.pop("next", "") or ""

    try:
        form = LoginForm(**{k: v for k, v in raw.items() if k in LoginForm.model_fields})
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/login.html",
            context=_auth_context(
                request,
                page_title="Sign In - mediBook",
                errors=_validation_errors(exc),
                form_values=raw,
                next_url=next_url,
            ),
            status_code=422,
        )

    try:
        user = authenticate_user(db, form)
    except AuthError as exc:
        errors = {exc.field or "email": exc.message}
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/login.html",
            context=_auth_context(
                request,
                page_title="Sign In - mediBook",
                errors=errors,
                form_values={"email": form.email, "remember_me": form.remember_me},
                next_url=next_url,
            ),
            status_code=422,
        )

    login_user(request, user.id, form.remember_me, role=user.role)
    set_flash(request, f"Welcome back, {user.first_name}!")
    redirect_to = resolve_login_redirect(user, next_url)
    return RedirectResponse(url=redirect_to, status_code=303)


# ── Register (patients only) ───────────────────────────────

@auth_router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/auth/register.html",
        context=_auth_context(request, page_title="Create Account - mediBook"),
    )


@auth_router.post("/register")
async def register_submit(request: Request, db: Session = Depends(get_db)):
    raw = await _parse_form(request)

    try:
        form = RegisterForm(**{k: v for k, v in raw.items() if k in RegisterForm.model_fields})
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/register.html",
            context=_auth_context(
                request,
                page_title="Create Account - mediBook",
                errors=_validation_errors(exc),
                form_values=raw,
            ),
            status_code=422,
        )

    try:
        user = register_patient(db, form)
    except AuthError as exc:
        errors = {exc.field or "email": exc.message}
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/register.html",
            context=_auth_context(
                request,
                page_title="Create Account - mediBook",
                errors=errors,
                form_values=raw,
            ),
            status_code=422,
        )

    login_user(request, user.id, remember_me=True, role=user.role)
    set_flash(request, "Your account has been created. Welcome to mediBook!")
    return RedirectResponse(url=get_post_login_redirect(user), status_code=303)


# ── Forgot password ────────────────────────────────────────

@auth_router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="pages/auth/forgot_password.html",
        context=_auth_context(request, page_title="Forgot Password - mediBook"),
    )


@auth_router.post("/forgot-password")
async def forgot_password_submit(request: Request, db: Session = Depends(get_db)):
    raw = await _parse_form(request)

    try:
        form = ForgotPasswordForm(**raw)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/forgot_password.html",
            context=_auth_context(
                request,
                page_title="Forgot Password - mediBook",
                errors=_validation_errors(exc),
                form_values=raw,
            ),
            status_code=422,
        )

    token_record = create_password_reset(db, form)

    if settings.debug and token_record:
        reset_url = f"/reset-password?token={token_record.token}"
        logger.info("DEV reset link for %s: %s", form.email, reset_url)

    return templates.TemplateResponse(
        request=request,
        name="pages/auth/forgot_password.html",
        context=_auth_context(
            request,
            page_title="Forgot Password - mediBook",
            success=True,
            dev_reset_url=f"/reset-password?token={token_record.token}" if settings.debug and token_record else None,
        ),
    )


# ── Reset password ─────────────────────────────────────────

@auth_router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str = "", db: Session = Depends(get_db)):
    valid = bool(token and get_valid_reset_token(db, token))
    return templates.TemplateResponse(
        request=request,
        name="pages/auth/reset_password.html",
        context=_auth_context(
            request,
            page_title="Reset Password - mediBook",
            token=token,
            token_valid=valid,
        ),
    )


@auth_router.post("/reset-password")
async def reset_password_submit(request: Request, db: Session = Depends(get_db)):
    raw = await _parse_form(request)

    try:
        form = ResetPasswordForm(**raw)
    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/reset_password.html",
            context=_auth_context(
                request,
                page_title="Reset Password - mediBook",
                errors=_validation_errors(exc),
                token=raw.get("token", ""),
                token_valid=True,
            ),
            status_code=422,
        )

    try:
        user = reset_password(db, form)
    except AuthError as exc:
        return templates.TemplateResponse(
            request=request,
            name="pages/auth/reset_password.html",
            context=_auth_context(
                request,
                page_title="Reset Password - mediBook",
                errors={exc.field or "token": exc.message},
                token=form.token,
                token_valid=False,
            ),
            status_code=422,
        )

    set_flash(request, "Your password has been reset. Please sign in.")
    return RedirectResponse(url="/login", status_code=303)


# ── Logout ─────────────────────────────────────────────────

@auth_router.post("/logout")
async def logout(request: Request):
    logout_user(request)
    set_flash(request, "You have been signed out.", category="info")
    return RedirectResponse(url="/", status_code=303)
