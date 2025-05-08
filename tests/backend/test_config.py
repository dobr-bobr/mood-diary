import os
import pytest
from fastapi.testclient import TestClient

from mood_diary.backend.config import Settings
from mood_diary.backend.app import get_app

RELEVANT_ENV_VARS = [
    "APP_TITLE",
    "APP_DESCRIPTION",
    "PASSWORD_HASHING_ENCODING",
    "PASSWORD_HASHING_HASH_NAME",
    "PASSWORD_HASHING_HASH_ITERATIONS",
    "PASSWORD_HASHING_SALT_SIZE",
    "PASSWORD_HASHING_SPLIT_CHAR",
    "AUTH_TOKEN_SECRET_KEY",
    "AUTH_TOKEN_ALGORITHM",
    "AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES",
    "AUTH_TOKEN_REFRESH_TOKEN_EXPIRE_MINUTES",
    "ROOT_PATH",
    "SQLITE_DB_PATH",
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
    # Explicitly unset APP_TITLE to ensure we test the default
    if "APP_TITLE" in os.environ:
        del os.environ["APP_TITLE"]
    # Explicitly unset APP_DESCRIPTION to ensure we test the default
    if "APP_DESCRIPTION" in os.environ:
        del os.environ["APP_DESCRIPTION"]
    # Explicitly unset PASSWORD_HASHING_ENCODING to ensure we test the default
    if "PASSWORD_HASHING_ENCODING" in os.environ:
        del os.environ["PASSWORD_HASHING_ENCODING"]
    # Explicitly unset PASSWORD_HASHING_HASH_NAME to ensure we test the default
    if "PASSWORD_HASHING_HASH_NAME" in os.environ:
        del os.environ["PASSWORD_HASHING_HASH_NAME"]
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
    assert settings.AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES == 360
    assert settings.ROOT_PATH == "/api"
    assert settings.SQLITE_DB_PATH == "data/mood_diary.db"


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


def test_app_startup_raises_exception_without_secret_key():
    """Tests that get_app raises an exception during startup if AUTH_TOKEN_SECRET_KEY is not set."""
    # Ensure the secret key is not set in the environment
    if "AUTH_TOKEN_SECRET_KEY" in os.environ:
        del os.environ["AUTH_TOKEN_SECRET_KEY"]

    settings = Settings()
    # Explicitly set to empty string or None if default is not empty
    settings.AUTH_TOKEN_SECRET_KEY = ""

    # Attempt to create the app instance first
    app = get_app(settings)

    # Use TestClient as a context manager to trigger startup/shutdown events
    with pytest.raises(
        Exception,
        match="Please set AUTH_TOKEN_SECRET_KEY environment variable",
    ):
        with TestClient(app) as client:
            pass
