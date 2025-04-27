import sqlite3
from uuid import UUID

from fastapi import Header, Depends

from mood_diary.backend.config import config
from mood_diary.backend.exceptions.user import InvalidOrExpiredAccessToken
from mood_diary.backend.repositories.mood import MoodStampRepository
from mood_diary.backend.repositories.sqlite.mood import SQLiteMoodRepository
from mood_diary.backend.repositories.sqlite.user import SQLiteUserRepository
from mood_diary.backend.repositories.user import UserRepository
from mood_diary.backend.services.mood import MoodService
from mood_diary.backend.services.user import UserService
from mood_diary.backend.utils.password_hasher import (
    SaltPasswordHasher,
    PasswordHasher,
)
from mood_diary.backend.utils.token_manager import (
    JWTTokenManager,
    TokenManager,
    TokenType,
)


def get_token_manager() -> TokenManager:
    return JWTTokenManager(
        config.AUTH_TOKEN_SECRET_KEY,
        config.AUTH_TOKEN_ALGORITHM,
        config.AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES,
        config.AUTH_TOKEN_REFRESH_TOKEN_EXPIRE_MINUTES,
    )


def get_password_hasher() -> PasswordHasher:
    return SaltPasswordHasher(
        config.PASSWORD_HASHING_ENCODING,
        config.PASSWORD_HASHING_SALT_SIZE,
        config.PASSWORD_HASHING_HASH_NAME,
        config.PASSWORD_HASHING_HASH_ITERATIONS,
        config.PASSWORD_HASHING_SPLIT_CHAR,
    )


def get_current_user_id(
    authorization: str | None = Header(None),
    token_manager: TokenManager = Depends(get_token_manager),
) -> UUID:
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidOrExpiredAccessToken()

    token = authorization.removeprefix("Bearer ").strip()
    payload = token_manager.decode_token(token)

    if payload is None or payload.type != TokenType.ACCESS:
        raise InvalidOrExpiredAccessToken()

    return payload.user_id


def get_connection():
    conn = sqlite3.connect(config.SQLITE_DB_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def get_user_repository(
    conn: sqlite3.Connection = Depends(get_connection),
) -> UserRepository:
    return SQLiteUserRepository(conn)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    password_hasher: PasswordHasher = Depends(get_password_hasher),
    token_manager: TokenManager = Depends(get_token_manager),
) -> UserService:
    return UserService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_manager=token_manager,
    )


def get_moodstamp_repository(
    conn: sqlite3.Connection = Depends(get_connection),
) -> MoodStampRepository:
    return SQLiteMoodRepository(conn)


def get_mood_service(
    moodstamp_repository: MoodStampRepository = Depends(
        get_moodstamp_repository
    ),
) -> MoodService:
    return MoodService(moodstamp_repository)
