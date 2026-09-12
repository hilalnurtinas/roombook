from datetime import datetime

from pydantic import BaseModel, model_validator


class BookingCreate(BaseModel):
    room_id: int
    start_at: datetime
    end_at: datetime

    @model_validator(mode="after")
    def end_after_start(self) -> "BookingCreate":
        if self.end_at <= self.start_at:
            raise ValueError("end_at must be after start_at")
        return self


class BookingRead(BaseModel):
    id: int
    room_id: int
    user_id: int
    start_at: datetime
    end_at: datetime
    status: str


class ConflictingBooking(BaseModel):
    start_at: datetime
    end_at: datetime


class SuggestedSlot(BaseModel):
    start_at: datetime
    end_at: datetime
