"""Email dispatch - simulated when SMTP is not configured."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def is_email_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_email(*, to_email: str, subject: str, body: str) -> bool:
    """Send an email. Simulates delivery when SMTP is not configured."""
    if not settings.email_reminders_enabled:
        logger.info("Email reminders disabled - skipped: %s", subject)
        return False

    if not is_email_configured():
        logger.info(
            "[EMAIL SIMULATION] To: %s | Subject: %s | Body: %s",
            to_email,
            subject,
            body[:200] + ("…" if len(body) > 200 else ""),
        )
        return True

    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.send_message(message)
        logger.info("Email sent to %s - %s", to_email, subject)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
