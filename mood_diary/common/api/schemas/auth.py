from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class Profile(BaseModel):
    id: UUID
    username: str
    name: str
    created_at: datetime
    updated_at: datetime
    password_updated_at: datetime


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=32)
    name: str = Field(..., min_length=3, max_length=32)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    password: str = Field(..., min_length=8, max_length=32)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class RefreshResponse(BaseModel):
    access_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8, max_length=32)
    new_password: str = Field(..., min_length=8, max_length=32)


class ChangeProfileRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=32)
