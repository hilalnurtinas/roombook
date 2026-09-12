from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingRead
from app.services.booking import create_booking

router = APIRouter()


@router.post("/bookings", response_model=BookingRead, status_code=201)
async def create_booking_endpoint(
    payload: BookingCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> BookingRead:
    booking = await create_booking(session, current_user, payload)
    return BookingRead(
        id=booking.id,
        room_id=booking.room_id,
        user_id=booking.user_id,
        start_at=booking.start_at,
        end_at=booking.end_at,
        status=booking.status,
    )
