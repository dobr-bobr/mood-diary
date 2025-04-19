from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class User(BaseModel):
    id: UUID
    username: str
    name: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    password_updated_at: datetime


class CreateUser(BaseModel):
    username: str
    name: str
    hashed_password: str


class UpdateUserProfile(BaseModel):
    name: str | None = None


class UpdateUserHashedPassword(BaseModel):
    hashed_password: str
