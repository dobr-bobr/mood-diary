from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel, Field


class RecordRequest(BaseModel):
    user_id: UUID
    date: date
    value: int = Field(..., max_digits=2)
    note: str | None = None


class UpdateRequest(BaseModel):
    user_id: UUID
    value: int | None = None
    note: str | None = None


class GetRequest(BaseModel):
    user_id: UUID
    date: date


class GetManyRequest(BaseModel):
    user_id: UUID
    start_date: date
    end_date: date
