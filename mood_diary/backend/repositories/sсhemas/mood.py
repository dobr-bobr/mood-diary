from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel


class MoodStamp(BaseModel):
    id: UUID
    user_id: UUID
    date: date
    value: int
    note: str
    created_at: datetime
    updated_at: datetime


class CreateMoodStamp(BaseModel):
    date: date
    user_id: UUID
    value: int
    note: str | None = None


class UpdateMoodStamp(BaseModel):
    value: int | None = None
    note: str | None = None
    user_id: UUID


class MoodStampFilter(BaseModel):
    user_id: UUID
    start_date: date
    end_date: date
