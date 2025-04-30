import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends, Cookie, status
from fastapi.testclient import TestClient

from mood_diary.backend.config import Settings
from mood_diary.backend.exceptions.user import (
    IncorrectOldPassword,
    IncorrectPasswordOrUserDoesNotExists,
    InvalidOrExpiredAccessToken,
    UsernameAlreadyExists,
    UserNotFound,
)
from mood_diary.backend.app import get_app
from mood_diary.backend.routes.dependencies import (
    get_current_user_id,
    get_token_manager,
    get_user_service,
)
from mood_diary.backend.services.user import UserService
from mood_diary.backend.utils.token_manager import (
    JWTTokenManager,
    TokenManager,
    TokenType,
)
from mood_diary.common.api.schemas.auth import (
    LoginResponse,
    Profile,
)


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def test_token_manager() -> TokenManager:
    """A fixture providing a TokenManager with fixed test settings."""
    return JWTTokenManager(
        secret_key="fixed-test-secret-key",
        algorithm="HS256",
        access_token_exp_minutes=5,
    )


@pytest.fixture
def main_app():
    return get_app(Settings(AUTH_TOKEN_SECRET_KEY="fixed-test-secret-key"))


@pytest.fixture
def override_dependencies(
    mock_user_service: AsyncMock, test_token_manager: TokenManager, main_app
):
    test_user_id = uuid.uuid4()

    async def mock_get_current_user_id_simple_check(
        access_token: str | None = Cookie(None),
        token_manager: TokenManager = Depends(lambda: test_token_manager),
    ) -> uuid.UUID:
        if not access_token:
            raise InvalidOrExpiredAccessToken()

        return test_user_id

    main_app.dependency_overrides[get_user_service] = lambda: mock_user_service
    main_app.dependency_overrides[get_token_manager] = (
        lambda: test_token_manager
    )
    main_app.dependency_overrides[get_current_user_id] = (
        mock_get_current_user_id_simple_check
    )

    yield test_user_id

    main_app.dependency_overrides = {}


@pytest.fixture
def client(override_dependencies, main_app):
    with TestClient(main_app) as c:
        yield c


@pytest.fixture
def sample_profile_data():
    now = datetime.now(timezone.utc)
    now_iso = now.isoformat().replace("+00:00", "Z")
    return {
        "id": str(uuid.uuid4()),
        "username": "testuser",
        "name": "Test User",
        "created_at": now_iso,
        "updated_at": now_iso,
        "password_updated_at": now_iso,
    }


def test_register_success(
    client: TestClient, mock_user_service: AsyncMock, sample_profile_data
):
    mock_user_service.register.return_value = Profile(**sample_profile_data)
    register_payload = {
        "username": "testuser",
        "password": "password123",
        "name": "Test User",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_profile_data
    mock_user_service.register.assert_awaited_once()


def test_register_username_exists(
    client: TestClient, mock_user_service: AsyncMock
):
    mock_user_service.register.side_effect = UsernameAlreadyExists()
    register_payload = {
        "username": "existinguser",
        "password": "password123",
        "name": "Test User",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Username already exists"}


def test_register_validation_error(client: TestClient):
    register_payload = {
        "username": "us",
        "password": "pass",
        "name": "Te",
    }
    response = client.post("/api/auth/register", json=register_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_success(client: TestClient, mock_user_service: AsyncMock):
    login_response_data = {
        "access_token": "fake_access_token",
    }
    mock_user_service.login.return_value = LoginResponse(**login_response_data)
    login_payload = {"username": "testuser", "password": "password123"}
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    assert "access_token" in response.cookies
    access_cookie = response.cookies.get("access_token")
    assert access_cookie is not None
    mock_user_service.login.assert_awaited_once()


def test_login_unauthorized(client: TestClient, mock_user_service: AsyncMock):
    mock_user_service.login.side_effect = (
        IncorrectPasswordOrUserDoesNotExists()
    )
    login_payload = {"username": "testuser", "password": "wrongpassword"}
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {
        "detail": "Incorrect password or username does not exist"
    }


def test_validate_token_success(client: TestClient, override_dependencies):
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.post("/api/auth/validate")
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b""


def test_validate_token_no_cookie(client: TestClient, override_dependencies):
    response = client.post("/api/auth/validate")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_get_profile_success(
    client: TestClient,
    mock_user_service: AsyncMock,
    sample_profile_data,
    override_dependencies,
):
    user_id = override_dependencies
    mock_user_service.get_profile.return_value = Profile(**sample_profile_data)
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.get("/api/auth/profile")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_profile_data
    mock_user_service.get_profile.assert_awaited_once_with(user_id)


def test_get_profile_unauthorized(client: TestClient, override_dependencies):
    response = client.get("/api/auth/profile")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_change_password_success(
    client: TestClient, mock_user_service: AsyncMock, override_dependencies
):
    user_id = override_dependencies
    mock_user_service.change_password.return_value = None
    password_payload = {
        "old_password": "oldPass123",
        "new_password": "newPass456!",
    }
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put(
        "/api/auth/password", json=password_payload
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json() is None
    mock_user_service.change_password.assert_awaited_once()
    call_args = mock_user_service.change_password.call_args[0]
    assert call_args[0] == user_id
    assert call_args[1].old_password == "oldPass123"
    assert call_args[1].new_password == "newPass456!"


def test_change_password_incorrect_old(
    client: TestClient, mock_user_service: AsyncMock, override_dependencies
):
    user_id = override_dependencies
    mock_user_service.change_password.side_effect = IncorrectOldPassword()
    password_payload = {
        "old_password": "wrongOldPass",
        "new_password": "newPass456!",
    }
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put(
        "/api/auth/password", json=password_payload
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect old password"}


def test_change_password_validation_error(
    client: TestClient, override_dependencies
):
    password_payload = {
        "old_password": "ValidOld1",
        "new_password": "short",
    }
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put(
        "/api/auth/password", json=password_payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_profile_success(
    client: TestClient,
    mock_user_service: AsyncMock,
    sample_profile_data,
    override_dependencies,
):
    user_id = override_dependencies
    updated_profile_data = sample_profile_data.copy()
    updated_profile_data["name"] = "New Name"
    updated_profile_data["updated_at"] = (
        datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    )
    mock_user_service.update_profile.return_value = Profile(
        **updated_profile_data
    )

    profile_payload = {"name": "New Name"}
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put(
        "/api/auth/profile", json=profile_payload
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == updated_profile_data
    mock_user_service.update_profile.assert_awaited_once()
    call_args = mock_user_service.update_profile.call_args[0]
    assert call_args[0] == user_id
    assert call_args[1].name == "New Name"


def test_update_profile_validation_error(
    client: TestClient, override_dependencies
):
    profile_payload = {"name": "N"}
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put(
        "/api/auth/profile", json=profile_payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
