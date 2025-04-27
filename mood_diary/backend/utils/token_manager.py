from abc import ABC, abstractmethod
from datetime import datetime, timedelta, UTC
from enum import Enum
from uuid import UUID

import jwt
from pydantic import BaseModel


class TokenType(str, Enum):
    ACCESS = "ACCESS"
    REFRESH = "REFRESH"


class TokenPayload(BaseModel):
    type: TokenType
    user_id: UUID
    iat: int
    exp: int


class TokenManager(ABC):
    @abstractmethod
    def create_token(self, token_type: TokenType, user_id: UUID) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> TokenPayload | None:
        pass

    @abstractmethod
    def is_token_valid(self, token: str) -> bool:
        pass

    @abstractmethod
    def get_token_type(self, token: str) -> TokenType | None:
        pass


class JWTTokenManager(TokenManager):
    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_token_exp_minutes: int,
        refresh_token_exp_minutes: int,
    ):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_exp = timedelta(minutes=access_token_exp_minutes)
        self.refresh_token_exp = timedelta(minutes=refresh_token_exp_minutes)

    def create_token(self, token_type: TokenType, user_id: UUID) -> str:
        now = datetime.now(UTC)

        if token_type == TokenType.ACCESS:
            exp = now + self.access_token_exp
        else:
            exp = now + self.refresh_token_exp

        payload = TokenPayload(
            type=token_type,
            user_id=user_id,
            iat=int(now.timestamp()),
            exp=int(exp.timestamp()),
        )

        return jwt.encode(
            payload.model_dump(mode="json"),
            self.secret_key,
            algorithm=self.algorithm,
        )

    def decode_token(self, token: str) -> TokenPayload | None:
        try:
            decoded = jwt.decode(
                token, self.secret_key, algorithms=[self.algorithm]
            )
            decoded["user_id"] = UUID(decoded["user_id"])
            return TokenPayload(**decoded)
        except jwt.ExpiredSignatureError:
            # TODO: Add logging
            pass
        except jwt.InvalidTokenError:
            # TODO: Add logging
            pass
        except Exception as e:
            # TODO: Add logging
            _ = e
            pass

        return None

    def is_token_valid(self, token: str) -> bool:
        return self.decode_token(token) is not None

    def get_token_type(self, token: str) -> TokenType | None:
        payload = self.decode_token(token)
        return payload.type if payload else None
