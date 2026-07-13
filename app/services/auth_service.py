"""Authentication business logic."""

from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.security import hash_password, verify_password
from app.models import PasswordResetToken, User
from app.models.enums import UserRole
from app.schemas.auth import ForgotPasswordForm, LoginForm, RegisterForm, ResetPasswordForm
from app.utils.helpers import utcnow

logger = logging.getLogger(__name__)

RESET_TOKEN_HOURS = 1
SESSION_MAX_AGE_DEFAULT = 60 * 60 * 24 * 7       # 7 days
SESSION_MAX_AGE_REMEMBER = 60 * 60 * 24 * 30     # 30 days


class AuthError(Exception):
    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower().strip()))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def register_patient(db: Session, form: RegisterForm) -> User:
    email = form.email.lower().strip()
    if get_user_by_email(db, email):
        raise AuthError("An account with this email already exists", field="email")

    user = User(
        first_name=form.first_name.strip(),
        last_name=form.last_name.strip(),
        email=email,
        phone=form.phone,
        password_hash=hash_password(form.password),
        role=UserRole.PATIENT.value,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, form: LoginForm) -> User:
    user = get_user_by_email(db, form.email)
    if not user or not verify_password(form.password, user.password_hash):
        raise AuthError("Invalid email or password", field="email")

    if not user.is_active:
        raise AuthError("Your account has been deactivated. Contact support.", field="email")

    return user


def create_password_reset(db: Session, form: ForgotPasswordForm) -> PasswordResetToken | None:
    """Create reset token if user exists. Returns None if email not found (no leak)."""
    user = get_user_by_email(db, form.email)
    if not user:
        return None

    # Invalidate existing unused tokens
    for token in user.password_resets:
        if token.used_at is None:
            token.used_at = utcnow()

    reset_token = PasswordResetToken(
        user_id=user.id,
        token=secrets.token_urlsafe(48),
        expires_at=utcnow() + timedelta(hours=RESET_TOKEN_HOURS),
    )
    db.add(reset_token)
    db.commit()
    db.refresh(reset_token)
    return reset_token


def get_valid_reset_token(db: Session, token: str) -> PasswordResetToken | None:
    record = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token == token)
    )
    if record and record.is_valid:
        return record
    return None


def reset_password(db: Session, form: ResetPasswordForm) -> User:
    record = get_valid_reset_token(db, form.token)
    if not record:
        raise AuthError("This reset link is invalid or has expired", field="token")

    user = record.user
    user.password_hash = hash_password(form.password)
    record.used_at = utcnow()
    db.commit()
    db.refresh(user)
    return user


def session_max_age(remember_me: bool) -> int:
    return SESSION_MAX_AGE_REMEMBER if remember_me else SESSION_MAX_AGE_DEFAULT


def get_post_login_redirect(user: User) -> str:
    return get_dashboard_path_for_role(user.role)


def get_dashboard_path_for_role(role: str) -> str:
    if role == UserRole.ADMIN.value:
        return "/admin/dashboard"
    if role == UserRole.DOCTOR.value:
        return "/doctor/dashboard"
    return "/patient/dashboard"


_GENERIC_LOGIN_NEXT = frozenset({"/", "", "/login", "/register", "/login/", "/register/"})


def resolve_login_redirect(user: User, next_url: str | None) -> str:
    """Send users to their role dashboard unless login was triggered from a specific page."""
    cleaned = (next_url or "").strip()
    if cleaned in _GENERIC_LOGIN_NEXT:
        return get_post_login_redirect(user)
    if cleaned.startswith("/") and not cleaned.startswith("//"):
        return cleaned
    return get_post_login_redirect(user)
