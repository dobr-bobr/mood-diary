import os
import pytest

from mood_diary.backend.config import Settings

RELEVANT_ENV_VARS = [
    "APP_TITLE", "APP_DESCRIPTION", "PASSWORD_HASHING_ENCODING",
    "PASSWORD_HASHING_HASH_NAME", "PASSWORD_HASHING_HASH_ITERATIONS",
    "PASSWORD_HASHING_SALT_SIZE", "PASSWORD_HASHING_SPLIT_CHAR",
    "AUTH_TOKEN_SECRET_KEY", "AUTH_TOKEN_ALGORITHM",
    "AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES",
    "AUTH_TOKEN_REFRESH_TOKEN_EXPIRE_MINUTES", "ROOT_PATH",
    "SQLITE_DB_PATH"
]

@pytest.fixture(autouse=True)
def manage_environ():
    """Manages environment variables for Settings tests."""
    original_values = {}
    for var in RELEVANT_ENV_VARS:
        if var in os.environ:
            original_values[var] = os.environ[var]
            del os.environ[var]
        else:
            original_values[var] = None

    yield

    for var in RELEVANT_ENV_VARS:
        original_value = original_values[var]
        if original_value is not None:
            os.environ[var] = original_value
        elif var in os.environ:
            del os.environ[var]


def test_settings_default_values():
    """Tests that Settings load default values correctly when no env vars are set."""
    settings = Settings()

    assert settings.APP_TITLE == "Mood Diary"
    assert settings.APP_DESCRIPTION == "Mood Diary API"
    assert settings.PASSWORD_HASHING_ENCODING == "utf-8"
    assert settings.PASSWORD_HASHING_HASH_NAME == "sha256"
    assert settings.PASSWORD_HASHING_HASH_ITERATIONS == 100000
    assert settings.PASSWORD_HASHING_SALT_SIZE == 16
    assert settings.PASSWORD_HASHING_SPLIT_CHAR == "$"
    assert settings.AUTH_TOKEN_SECRET_KEY == ""
    assert settings.AUTH_TOKEN_ALGORITHM == "HS256"
    assert settings.AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert settings.AUTH_TOKEN_REFRESH_TOKEN_EXPIRE_MINUTES == 60 * 24 * 30
    assert settings.ROOT_PATH == "/api"
    assert settings.SQLITE_DB_PATH == "mood_diary.db"


def test_settings_override_with_env_vars():
    """Tests that Settings can be overridden by environment variables."""
    os.environ["APP_TITLE"] = "My Custom App"
    os.environ["AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
    os.environ["PASSWORD_HASHING_HASH_ITERATIONS"] = "150000"

    settings = Settings()

    assert settings.APP_TITLE == "My Custom App"
    assert settings.AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES == 60
    assert settings.PASSWORD_HASHING_HASH_ITERATIONS == 150000
    assert settings.PASSWORD_HASHING_ENCODING == "utf-8"
