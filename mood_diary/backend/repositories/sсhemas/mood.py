from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

class MoodStamp(BaseModel):
    id: UUID
    user_id: UUID
    entry_time: datetime
    type: int
    note: str
    created_at: datetime
    updated_at: datetime

class CreateMoodStamp(BaseModel):
    user_id: UUID
    entry_time: datetime
    type: int
    note: str

class UpdateMoodType(BaseModel):
    type: int

class UpdateMoodNote(BaseModel):
    note: str
