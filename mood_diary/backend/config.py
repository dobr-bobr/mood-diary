from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_TITLE: str = "Mood Diary"
    APP_DESCRIPTION: str = "Mood Diary API"

    PASSWORD_HASHING_ENCODING: str = "utf-8"
    PASSWORD_HASHING_HASH_NAME: str = "sha256"
    PASSWORD_HASHING_HASH_ITERATIONS: int = 100000
    PASSWORD_HASHING_SALT_SIZE: int = 16
    PASSWORD_HASHING_SPLIT_CHAR: str = "$"

    AUTH_TOKEN_SECRET_KEY: str = ""
    AUTH_TOKEN_ALGORITHM: str = "HS256"
    AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES: int = 360
    AUTH_SECURE_COOKIE: bool = False

    ROOT_PATH: str = "/api"

    SQLITE_DB_PATH: str = "data/mood_diary.db"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_CACHE_TTL: int = 60  # seconds

    # Logging configuration
    LOGGING_LEVEL: str = "INFO"
    LOGGING_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    LOGGING_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


config = Settings()
