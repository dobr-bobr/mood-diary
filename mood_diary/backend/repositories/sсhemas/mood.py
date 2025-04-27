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
    note: str


class UpdateMoodStamp(BaseModel):
    value: int | None = None
    note: str | None = None


class MoodStampFilter(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    value: int | None = None
