from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import PENDING, Booking
from app.models.room import Room
from app.models.user import User


async def make_user(session: AsyncSession, *, id: int, name: str = "Test User") -> User:
    user = User(id=id, name=name)
    session.add(user)
    await session.flush()
    return user


async def make_room(
    session: AsyncSession, *, id: int, owner_id: int, name: str = "Room", capacity: int = 4
) -> Room:
    room = Room(id=id, name=name, capacity=capacity, owner_id=owner_id)
    session.add(room)
    await session.flush()
    return room


async def make_booking(
    session: AsyncSession,
    *,
    room_id: int,
    user_id: int,
    start_at: datetime,
    end_at: datetime,
    status: str = PENDING,
) -> Booking:
    booking = Booking(
        room_id=room_id, user_id=user_id, start_at=start_at, end_at=end_at, status=status
    )
    session.add(booking)
    await session.flush()
    return booking
