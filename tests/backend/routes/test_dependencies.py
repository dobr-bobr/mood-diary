import sqlite3
import uuid
from unittest.mock import MagicMock, patch

import pytest

from mood_diary.backend.config import config
from mood_diary.backend.exceptions.user import InvalidOrExpiredAccessToken
from mood_diary.backend.repositories.sqlite.user import SQLiteUserRepository
from mood_diary.backend.repositories.user import UserRepository
from mood_diary.backend.routes import dependencies
from mood_diary.backend.services.user import UserService
from mood_diary.backend.utils.password_hasher import (
    PasswordHasher,
    SaltPasswordHasher,
)
from mood_diary.backend.utils.token_manager import (
    JWTTokenManager,
    TokenManager,
    TokenPayload,
    TokenType,
)

AUTH_TOKEN_SECRET_KEY = "test-secret-for-pytest"
SQLITE_DB_PATH = ":memory:"


def test_get_token_manager(monkeypatch):
    """Test that get_token_manager creates JWTTokenManager with correct config."""
    test_secret = "test-secret-key-for-this-test"
    test_algo = "HS512"
    test_access_exp = 15

    monkeypatch.setattr(config, "AUTH_TOKEN_SECRET_KEY", test_secret)
    monkeypatch.setattr(config, "AUTH_TOKEN_ALGORITHM", test_algo)
    monkeypatch.setattr(
        config, "AUTH_TOKEN_ACCESS_TOKEN_EXPIRE_MINUTES", test_access_exp
    )

    token_manager = dependencies.get_token_manager()

    assert isinstance(token_manager, JWTTokenManager)
    assert token_manager.secret_key == test_secret
    assert token_manager.algorithm == test_algo
    assert (
        token_manager.access_token_exp.total_seconds() == test_access_exp * 60
    )


def test_get_password_hasher(monkeypatch):
    """Test that get_password_hasher creates SaltPasswordHasher with correct config."""
    monkeypatch.setattr(config, "PASSWORD_HASHING_ENCODING", "ascii")
    monkeypatch.setattr(config, "PASSWORD_HASHING_SALT_SIZE", 8)
    monkeypatch.setattr(config, "PASSWORD_HASHING_HASH_NAME", "md5")
    monkeypatch.setattr(config, "PASSWORD_HASHING_HASH_ITERATIONS", 1000)
    monkeypatch.setattr(config, "PASSWORD_HASHING_SPLIT_CHAR", "#")

    password_hasher = dependencies.get_password_hasher()
    assert isinstance(password_hasher, SaltPasswordHasher)
    assert password_hasher.encoding == "ascii"
    assert password_hasher.salt_size == 8
    assert password_hasher.hash_name == "md5"
    assert password_hasher.hash_iterations == 1000
    assert password_hasher.split_char == "#"


def test_get_current_user_id_success():
    """Test successful user ID retrieval with valid token."""
    mock_token_manager = MagicMock(spec=TokenManager)
    test_user_id = uuid.uuid4()
    mock_token_manager.decode_token.return_value = TokenPayload(
        type=TokenType.ACCESS, user_id=test_user_id, iat=1000, exp=9999999999
    )
    user_id = dependencies.get_current_user_id(
        access_token="valid_token", token_manager=mock_token_manager
    )
    mock_token_manager.decode_token.assert_called_once_with("valid_token")
    assert user_id == test_user_id


def test_get_current_user_id_no_cookie():
    """Test raising exception when access_token cookie is missing."""
    mock_token_manager = MagicMock(spec=TokenManager)
    with pytest.raises(InvalidOrExpiredAccessToken):
        dependencies.get_current_user_id(
            access_token=None, token_manager=mock_token_manager
        )
    mock_token_manager.decode_token.assert_not_called()


def test_get_current_user_id_invalid_token():
    """Test raising exception when token decoding fails."""
    mock_token_manager = MagicMock(spec=TokenManager)
    mock_token_manager.decode_token.return_value = None
    with pytest.raises(InvalidOrExpiredAccessToken):
        dependencies.get_current_user_id(
            access_token="invalid_token",
            token_manager=mock_token_manager,
        )
    mock_token_manager.decode_token.assert_called_once_with("invalid_token")


def test_get_connection(monkeypatch):
    """Test the get_connection generator yields and closes connection."""
    monkeypatch.setattr(config, "SQLITE_DB_PATH", ":memory:")

    mock_conn = MagicMock(spec=sqlite3.Connection)

    with patch(
        "mood_diary.backend.routes.dependencies.sqlite3.connect",
        return_value=mock_conn,
    ) as mock_connect:
        conn_generator = dependencies.get_connection()
        conn_instance = None
        try:
            conn_instance = next(conn_generator)

            mock_connect.assert_called_once_with(
                ":memory:", check_same_thread=False
            )

            assert conn_instance is mock_conn

            mock_conn.close.assert_not_called()
        except Exception as e:
            pytest.fail(f"Generator raised unexpected exception: {e}")
        finally:
            with pytest.raises(StopIteration):
                next(conn_generator)

            if conn_instance:
                mock_conn.close.assert_called_once()


def test_get_user_repository():
    """Test get_user_repository creates SQLiteUserRepository with connection."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    user_repo = dependencies.get_user_repository(conn=mock_conn)
    assert isinstance(user_repo, SQLiteUserRepository)
    assert user_repo.connection is mock_conn


def test_get_user_service():
    """Test get_user_service creates UserService with dependencies."""
    mock_repo = MagicMock(spec=UserRepository)
    mock_hasher = MagicMock(spec=PasswordHasher)
    mock_manager = MagicMock(spec=TokenManager)
    user_service = dependencies.get_user_service(
        user_repository=mock_repo,
        password_hasher=mock_hasher,
        token_manager=mock_manager,
    )
    assert isinstance(user_service, UserService)
    assert user_service.user_repository is mock_repo
    assert user_service.password_hasher is mock_hasher
    assert user_service.token_manager is mock_manager
