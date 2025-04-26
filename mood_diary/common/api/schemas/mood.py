from datetime import date
from uuid import UUID

from pydantic import BaseModel, Field


class CreateMoodStampRequest(BaseModel):
    user_id: UUID
    date: date
    value: int = Field(..., max_digits=2)
    note: str | None = None


class UpdateMoodStampRequest(BaseModel):
    user_id: UUID
    value: int | None = None
    note: str | None = None


class GetMoodStampRequest(BaseModel):
    user_id: UUID
    date: date


class GetManyMoodStampsRequest(BaseModel):
    user_id: UUID
    start_date: date
    end_date: date
