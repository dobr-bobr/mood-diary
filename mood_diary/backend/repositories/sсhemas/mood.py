from datetime import datetime, date
from uuid import UUID

from pydantic import BaseModel

class MoodStamp(BaseModel):
    id: UUID
    user_id: UUID
    entry_date: date
    value: int
    note: str
    created_at: datetime
    updated_at: datetime

class CreateMoodStamp(BaseModel):
    entry_date: date
    value: int
    note: str

class UpdateMoodStamp(BaseModel):
    value: int
    note: str
