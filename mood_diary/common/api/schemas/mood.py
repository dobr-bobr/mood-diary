from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class MoodStampSchema(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    value: int
    note: str
    created_at: datetime
    updated_at: datetime


class CreateMoodStampRequest(BaseModel):
    date: date
    value: int = Field(..., ge=1, le=10)
    note: str


class UpdateMoodStampRequest(BaseModel):
    value: int | None = None
    note: str | None = None


class GetManyMoodStampsRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    value: int | None = None
