from app.schemas.booking import ConflictingBooking, SuggestedSlot


class AppError(Exception):
    """Base for typed domain errors. Never leak raw internals to clients."""

    status_code = 500
    message = "internal error"


class NotAuthorizedError(AppError):
    status_code = 403
    message = "not authorized"


class RoomNotFoundError(AppError):
    status_code = 404
    message = "room not found"


class UnresolvedUserError(AppError):
    status_code = 401
    message = "current user could not be resolved"


class BookingConflictError(AppError):
    status_code = 409
    message = "requested time range conflicts with an existing booking"

    def __init__(
        self,
        conflicts: list[ConflictingBooking],
        suggestions: list[SuggestedSlot],
    ) -> None:
        super().__init__(self.message)
        self.conflicts = conflicts
        self.suggestions = suggestions
