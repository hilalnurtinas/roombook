class AppError(Exception):
    """Base for typed domain errors. Never leak raw internals to clients."""

    status_code = 500
    message = "internal error"


class NotAuthorizedError(AppError):
    status_code = 403
    message = "not authorized"
