"""Custom application exceptions."""


class AppException(Exception):
    """Base exception for domain-level errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ConflictError(AppException):
    """Raised when an operation conflicts with existing state."""

    def __init__(self, message: str = "Conflict"):
        super().__init__(message, status_code=409)


class UnauthorizedError(AppException):
    """Raised when authentication is required or invalid."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)
