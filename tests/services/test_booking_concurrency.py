import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.errors import BookingConflictError, RoomNotFoundError
from app.models.user import User
from app.schemas.booking import BookingCreate
from app.services.booking import create_booking
from tests.models.factories import make_room, make_user

T0 = datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
HOUR = timedelta(hours=1)


async def _book_and_commit(session: AsyncSession, user_id: int) -> str:
    user = await session.get(User, user_id)
    assert user is not None
    try:
        await create_booking(session, user, BookingCreate(room_id=1, start_at=T0, end_at=T0 + HOUR))
        await session.commit()
        return "succeeded"
    except (BookingConflictError, RoomNotFoundError):
        await session.rollback()
        return "rejected_by_app"
    except DBAPIError:
        await session.rollback()
        return "rejected_by_db"


async def test_concurrent_overlapping_requests_only_one_succeeds(
    two_real_sessions: tuple[AsyncSession, AsyncSession],
) -> None:
    session_a, session_b = two_real_sessions
    await make_user(session_a, id=1, name="Owner")
    await make_room(session_a, id=1, owner_id=1)
    await session_a.commit()
    await make_user(session_b, id=2, name="Requester")
    await session_b.commit()

    results = await asyncio.gather(
        _book_and_commit(session_a, 1),
        _book_and_commit(session_b, 2),
    )

    successes = [r for r in results if r == "succeeded"]
    rejections = [r for r in results if r != "succeeded"]
    assert len(successes) == 1
    assert len(rejections) == 1
