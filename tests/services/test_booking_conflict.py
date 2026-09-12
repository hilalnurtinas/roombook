from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import BookingConflictError, RoomNotFoundError
from app.models.booking import CANCELLED, PENDING, REJECTED
from app.schemas.booking import BookingCreate, ConflictingBooking
from app.services.booking import create_booking
from tests.models.factories import make_booking, make_room, make_user

T0 = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


async def _setup_room(session: AsyncSession, room_id: int = 1, owner_id: int = 1) -> None:
    await make_user(session, id=owner_id)
    await make_room(session, id=room_id, owner_id=owner_id)


async def test_booking_with_no_conflict_succeeds(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2, name="Bob")

    booking = await create_booking(
        test_session, user, BookingCreate(room_id=1, start_at=T0, end_at=T0 + HOUR)
    )

    assert booking.status == PENDING
    assert booking.room_id == 1
    assert booking.user_id == 2


async def test_full_containment_overlap_rejected(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + 3 * HOUR)

    with pytest.raises(BookingConflictError):
        await create_booking(
            test_session,
            user,
            BookingCreate(room_id=1, start_at=T0 + HOUR, end_at=T0 + 2 * HOUR),
        )


async def test_partial_start_overlap_rejected(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)

    with pytest.raises(BookingConflictError):
        await create_booking(
            test_session,
            user,
            BookingCreate(
                room_id=1,
                start_at=T0 - timedelta(minutes=30),
                end_at=T0 + timedelta(minutes=30),
            ),
        )


async def test_partial_end_overlap_rejected(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)

    with pytest.raises(BookingConflictError):
        await create_booking(
            test_session,
            user,
            BookingCreate(
                room_id=1,
                start_at=T0 + timedelta(minutes=30),
                end_at=T0 + timedelta(minutes=90),
            ),
        )


async def test_fully_contained_within_existing_rejected(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + 3 * HOUR)

    with pytest.raises(BookingConflictError):
        await create_booking(
            test_session,
            user,
            BookingCreate(room_id=1, start_at=T0, end_at=T0 + 3 * HOUR),
        )


async def test_back_to_back_boundaries_accepted(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)

    before = await create_booking(
        test_session,
        user,
        BookingCreate(room_id=1, start_at=T0 - HOUR, end_at=T0),
    )
    after = await create_booking(
        test_session,
        user,
        BookingCreate(room_id=1, start_at=T0 + HOUR, end_at=T0 + 2 * HOUR),
    )

    assert before.status == PENDING
    assert after.status == PENDING


async def test_unknown_room_raises_not_found(test_session: AsyncSession) -> None:
    user = await make_user(test_session, id=1)

    with pytest.raises(RoomNotFoundError):
        await create_booking(
            test_session,
            user,
            BookingCreate(room_id=999, start_at=T0, end_at=T0 + HOUR),
        )


async def test_overlap_on_different_room_not_a_conflict(test_session: AsyncSession) -> None:
    await make_user(test_session, id=1)
    await make_room(test_session, id=1, owner_id=1)
    await make_room(test_session, id=2, owner_id=1)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)
    user = await make_user(test_session, id=2)

    booking = await create_booking(
        test_session, user, BookingCreate(room_id=2, start_at=T0, end_at=T0 + HOUR)
    )

    assert booking.status == PENDING


async def test_cancelled_and_rejected_bookings_ignored(test_session: AsyncSession) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(
        test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR, status=CANCELLED
    )
    await make_booking(
        test_session,
        room_id=1,
        user_id=1,
        start_at=T0,
        end_at=T0 + HOUR,
        status=REJECTED,
    )

    booking = await create_booking(
        test_session, user, BookingCreate(room_id=1, start_at=T0, end_at=T0 + HOUR)
    )

    assert booking.status == PENDING


async def test_conflict_error_reports_conflicting_range_and_suggestions(
    test_session: AsyncSession,
) -> None:
    await _setup_room(test_session)
    user = await make_user(test_session, id=2)
    await make_booking(test_session, room_id=1, user_id=1, start_at=T0, end_at=T0 + HOUR)

    with pytest.raises(BookingConflictError) as excinfo:
        await create_booking(
            test_session, user, BookingCreate(room_id=1, start_at=T0, end_at=T0 + HOUR)
        )

    err = excinfo.value
    assert err.conflicts == [ConflictingBooking(start_at=T0, end_at=T0 + HOUR)]
    assert len(err.suggestions) >= 1
    assert err.suggestions[0].start_at == T0 + HOUR
