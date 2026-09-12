from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import BookingConflictError, RoomNotFoundError
from app.models.booking import INACTIVE_STATUSES, PENDING, Booking
from app.models.room import Room
from app.models.user import User
from app.schemas.booking import BookingCreate, ConflictingBooking
from app.services.slots import DEFAULT_WINDOW, find_free_slots


async def create_booking(
    session: AsyncSession, current_user: User, payload: BookingCreate
) -> Booking:
    room = await session.get(Room, payload.room_id)
    if room is None:
        raise RoomNotFoundError()

    # Active bookings across the whole slot-search window, not just ones overlapping the
    # original request — a suggested slot must avoid every booking in the window, not only
    # the one(s) that caused the original conflict.
    active_in_window = await _active_bookings_in_range(
        session, payload.room_id, payload.start_at, payload.start_at + DEFAULT_WINDOW
    )
    conflicting = [
        b for b in active_in_window if b.start_at < payload.end_at and b.end_at > payload.start_at
    ]
    if conflicting:
        suggestions = find_free_slots(
            existing=[(b.start_at, b.end_at) for b in active_in_window],
            requested_start=payload.start_at,
            duration=payload.end_at - payload.start_at,
        )
        raise BookingConflictError(
            conflicts=[
                ConflictingBooking(start_at=b.start_at, end_at=b.end_at) for b in conflicting
            ],
            suggestions=suggestions,
        )

    booking = Booking(
        room_id=payload.room_id,
        user_id=current_user.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
        status=PENDING,
    )
    session.add(booking)
    await session.flush()
    return booking


async def _active_bookings_in_range(
    session: AsyncSession, room_id: int, range_start: datetime, range_end: datetime
) -> list[Booking]:
    stmt = select(Booking).where(
        Booking.room_id == room_id,
        Booking.status.notin_(INACTIVE_STATUSES),
        Booking.start_at < range_end,
        Booking.end_at > range_start,
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
