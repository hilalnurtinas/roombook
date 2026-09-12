from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.errors import AppError, BookingConflictError
from app.routers.booking import router as booking_router
from app.routers.health import router as health_router

app = FastAPI(title="roombook")
app.include_router(health_router)
app.include_router(booking_router)


@app.exception_handler(BookingConflictError)
async def booking_conflict_handler(request: Request, exc: BookingConflictError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "conflicts": [c.model_dump(mode="json") for c in exc.conflicts],
            "suggestions": [s.model_dump(mode="json") for s in exc.suggestions],
        },
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
