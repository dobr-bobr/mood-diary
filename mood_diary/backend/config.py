from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "Mood Diary"
    APP_DESCRIPTION: str = "Mood Diary API"

    PASSWORD_HASHING_ENCODING: str = "utf-8"
    PASSWORD_HASHING_HASH_NAME: str = "sha256"
    PASSWORD_HASHING_HASH_ITERATIONS: int = 100000
    PASSWORD_HASHING_SALT_SIZE: int = 16
    PASSWORD_HASHING_SPLIT_CHAR: str = "$"

    AUTH_TOKEN_SECRET_KEY: str
    AUTH_TOKEN_ALGORITHM: str = "HS256"
    AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes
    AUTH_TOKEN_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days

    SQLITE_DB_PATH: str = "mood_diary.db"


config = Settings()
