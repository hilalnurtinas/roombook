from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.services.health import check_database

router = APIRouter()


@router.get("/health", response_model=None)
async def health(session: AsyncSession = Depends(get_session)) -> dict[str, str] | JSONResponse:
    try:
        await check_database(session)
    except (SQLAlchemyError, OSError):
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "connected"}
