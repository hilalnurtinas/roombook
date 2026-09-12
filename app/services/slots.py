from datetime import datetime, timedelta

from app.schemas.booking import SuggestedSlot

DEFAULT_WINDOW = timedelta(hours=24)
DEFAULT_LIMIT = 3


def find_free_slots(
    existing: list[tuple[datetime, datetime]],
    requested_start: datetime,
    duration: timedelta,
    window: timedelta = DEFAULT_WINDOW,
    limit: int = DEFAULT_LIMIT,
) -> list[SuggestedSlot]:
    """Find up to `limit` non-overlapping gaps of `duration`, starting at or after
    `requested_start`, within `requested_start + window`. `existing` need not be sorted
    and may contain bookings outside the window (ignored). Half-open ranges [start, end)
    match the DB exclusion constraint, so back-to-back bookings never count as a conflict.
    """
    window_end = requested_start + window
    relevant = sorted(
        (start, end) for start, end in existing if end > requested_start and start < window_end
    )

    slots: list[SuggestedSlot] = []
    cursor = requested_start
    for start, end in relevant:
        if len(slots) >= limit:
            return slots
        gap_end = min(start, window_end)
        if gap_end - cursor >= duration:
            slots.append(SuggestedSlot(start_at=cursor, end_at=cursor + duration))
            if len(slots) >= limit:
                return slots
        cursor = max(cursor, end)

    while len(slots) < limit and window_end - cursor >= duration:
        slots.append(SuggestedSlot(start_at=cursor, end_at=cursor + duration))
        cursor = cursor + duration

    return slots
