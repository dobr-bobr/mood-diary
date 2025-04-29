import uuid
from time import sleep
from unittest.mock import MagicMock, patch

import pytest
import jwt

from mood_diary.backend.utils.token_manager import (
    JWTTokenManager,
    TokenPayload,
    TokenType,
)

SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXP_MINUTES = 1
REFRESH_TOKEN_EXP_MINUTES = 5


@pytest.fixture(scope="module")
def token_manager() -> JWTTokenManager:
    return JWTTokenManager(
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        access_token_exp_minutes=ACCESS_TOKEN_EXP_MINUTES,
        refresh_token_exp_minutes=REFRESH_TOKEN_EXP_MINUTES,
    )


@pytest.fixture(scope="module")
def user_id() -> uuid.UUID:
    return uuid.uuid4()


def test_create_access_token(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.ACCESS, user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_refresh_token(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.REFRESH, user_id)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_valid_access_token(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.ACCESS, user_id)
    payload = token_manager.decode_token(token)

    assert payload is not None
    assert isinstance(payload, TokenPayload)
    assert payload.user_id == user_id
    assert payload.type == TokenType.ACCESS
    assert payload.exp > payload.iat


def test_decode_valid_refresh_token(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.REFRESH, user_id)
    payload = token_manager.decode_token(token)

    assert payload is not None
    assert isinstance(payload, TokenPayload)
    assert payload.user_id == user_id
    assert payload.type == TokenType.REFRESH
    assert payload.exp > payload.iat


def test_decode_invalid_token(token_manager: JWTTokenManager):
    invalid_token = "this.is.not.a.valid.token"
    payload = token_manager.decode_token(invalid_token)
    assert payload is None


def test_decode_expired_access_token(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    short_exp_manager = JWTTokenManager(
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        access_token_exp_minutes=0.001,
        refresh_token_exp_minutes=1,
    )
    token = short_exp_manager.create_token(TokenType.ACCESS, user_id)

    sleep(0.1)

    payload = short_exp_manager.decode_token(token)
    assert payload is None


def test_decode_token_wrong_secret(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.ACCESS, user_id)

    wrong_secret_manager = JWTTokenManager(
        secret_key="wrong-secret",
        algorithm=ALGORITHM,
        access_token_exp_minutes=ACCESS_TOKEN_EXP_MINUTES,
        refresh_token_exp_minutes=REFRESH_TOKEN_EXP_MINUTES,
    )

    payload = wrong_secret_manager.decode_token(token)
    assert payload is None


def test_is_token_valid_valid(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.ACCESS, user_id)
    assert token_manager.is_token_valid(token)


def test_is_token_valid_invalid(token_manager: JWTTokenManager):
    invalid_token = "invalid.token"
    assert not token_manager.is_token_valid(invalid_token)


def test_is_token_valid_expired(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    short_exp_manager = JWTTokenManager(
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        access_token_exp_minutes=0.001,
        refresh_token_exp_minutes=1,
    )
    token = short_exp_manager.create_token(TokenType.ACCESS, user_id)
    sleep(0.1)
    assert not short_exp_manager.is_token_valid(token)


def test_get_token_type_access(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.ACCESS, user_id)
    token_type = token_manager.get_token_type(token)
    assert token_type == TokenType.ACCESS


def test_get_token_type_refresh(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    token = token_manager.create_token(TokenType.REFRESH, user_id)
    token_type = token_manager.get_token_type(token)
    assert token_type == TokenType.REFRESH


def test_get_token_type_invalid(token_manager: JWTTokenManager):
    invalid_token = "invalid.token"
    token_type = token_manager.get_token_type(invalid_token)
    assert token_type is None


def test_get_token_type_expired(
    token_manager: JWTTokenManager, user_id: uuid.UUID
):
    short_exp_manager = JWTTokenManager(
        secret_key=SECRET_KEY,
        algorithm=ALGORITHM,
        access_token_exp_minutes=0.001,
        refresh_token_exp_minutes=1,
    )
    token = short_exp_manager.create_token(TokenType.ACCESS, user_id)
    sleep(0.1)
    token_type = short_exp_manager.get_token_type(token)
    assert token_type is None


@patch("jwt.decode")
def test_decode_token_unexpected_exception(
    mock_jwt_decode: MagicMock,
    token_manager: JWTTokenManager,
    user_id: uuid.UUID,
):
    """Test that decode_token handles unexpected exceptions gracefully."""
    mock_jwt_decode.side_effect = Exception("Unexpected error during decode")
    token = token_manager.create_token(TokenType.ACCESS, user_id)

    payload = token_manager.decode_token(token)

    assert payload is None
    mock_jwt_decode.assert_called_once_with(
        token, token_manager.secret_key, algorithms=[token_manager.algorithm]
    )


@patch("jwt.decode")
def test_get_token_type_unexpected_exception(
    mock_jwt_decode: MagicMock,
    token_manager: JWTTokenManager,
    user_id: uuid.UUID,
):
    """Test that get_token_type handles unexpected exceptions gracefully."""
    mock_jwt_decode.side_effect = Exception("Unexpected error during decode")
    token = token_manager.create_token(TokenType.ACCESS, user_id)

    token_type = token_manager.get_token_type(token)

    assert token_type is None
    mock_jwt_decode.assert_called_once()


@patch("jwt.decode")
def test_is_token_valid_unexpected_exception(
    mock_jwt_decode: MagicMock,
    token_manager: JWTTokenManager,
    user_id: uuid.UUID,
):
    """Test that is_token_valid handles unexpected exceptions gracefully."""
    mock_jwt_decode.side_effect = Exception("Unexpected error during decode")
    token = token_manager.create_token(TokenType.ACCESS, user_id)

    is_valid = token_manager.is_token_valid(token)

    assert is_valid is False
    mock_jwt_decode.assert_called_once()


@patch("jwt.decode")
def test_decode_catches_expired_signature_error(
    mock_jwt_decode: MagicMock,
    token_manager: JWTTokenManager,
    user_id: uuid.UUID,
):
    """Test that decode_token specifically returns None on ExpiredSignatureError."""
    mock_jwt_decode.side_effect = jwt.ExpiredSignatureError("Token has expired")
    token = "any_token_string"
    payload = token_manager.decode_token(token)
    assert payload is None
    mock_jwt_decode.assert_called_once()


@patch("jwt.decode")
def test_decode_catches_invalid_token_error(
    mock_jwt_decode: MagicMock,
    token_manager: JWTTokenManager,
    user_id: uuid.UUID,
):
    """Test that decode_token specifically returns None on InvalidTokenError."""
    mock_jwt_decode.side_effect = jwt.InvalidTokenError("Invalid token format")
    token = "any_token_string"
    payload = token_manager.decode_token(token)
    assert payload is None
    mock_jwt_decode.assert_called_once()
