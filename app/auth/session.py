"""Session helpers for cookie-based authentication."""

from fastapi import Request

SESSION_USER_KEY = "user_id"
SESSION_ROLE_KEY = "user_role"
SESSION_REMEMBER_KEY = "remember_me"
SESSION_FLASH_KEY = "flash"


def login_user(request: Request, user_id: int, remember_me: bool = False, role: str | None = None) -> None:
    request.session[SESSION_USER_KEY] = user_id
    request.session[SESSION_REMEMBER_KEY] = remember_me
    if role:
        request.session[SESSION_ROLE_KEY] = role


def logout_user(request: Request) -> None:
    request.session.pop(SESSION_USER_KEY, None)
    request.session.pop(SESSION_ROLE_KEY, None)
    request.session.pop(SESSION_REMEMBER_KEY, None)


def get_session_user_id(request: Request) -> int | None:
    user_id = request.session.get(SESSION_USER_KEY)
    return int(user_id) if user_id is not None else None


def set_flash(request: Request, message: str, category: str = "success") -> None:
    request.session[SESSION_FLASH_KEY] = {"message": message, "category": category}


def pop_flash(request: Request) -> dict | None:
    return request.session.pop(SESSION_FLASH_KEY, None)
