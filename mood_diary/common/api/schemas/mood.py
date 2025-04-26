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
    user_id: UUID
    date: date
    value: int = Field(..., max_digits=2)
    note: str | None = None


class UpdateMoodStampRequest(BaseModel):
    user_id: UUID
    date: date
    value: int | None = None
    note: str | None = None


class GetMoodStampRequest(BaseModel):
    user_id: UUID
    date: date


class GetManyMoodStampsRequest(BaseModel):
    user_id: UUID
    start_date: date
    end_date: date
    value: int
