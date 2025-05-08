from pydantic import BaseModel

from mood_diary.common.api.schemas.auth import LoginResponse


class TokenData(BaseModel):
	username: str | None = None


class TokenWithCSRF(LoginResponse):
	csrf_token: str
