# Stand-in for real authentication (spec 0002, Constraints #1). `X-User-Id` proves nothing about
# identity — it exists only so a booking can be attributed to a user before real JWT auth lands.
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.errors import UnresolvedUserError
from app.models.user import User


async def get_current_user(
    x_user_id: int | None = Header(default=None),
    session: AsyncSession = Depends(get_session),
) -> User:
    if x_user_id is None:
        raise UnresolvedUserError()
    user = await session.get(User, x_user_id)
    if user is None:
        raise UnresolvedUserError()
    return user
