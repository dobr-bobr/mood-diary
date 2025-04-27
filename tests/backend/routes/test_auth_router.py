import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import Depends, Header, status
from fastapi.testclient import TestClient

from mood_diary.backend.config import Settings
from mood_diary.backend.exceptions.user import (
    IncorrectOldPassword,
    IncorrectPasswordOrUserDoesNotExists,
    InvalidOrExpiredAccessToken,
    InvalidOrExpiredRefreshToken,
    UsernameAlreadyExists,
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
)
from mood_diary.common.api.schemas.auth import (
    LoginResponse,
    Profile,
    RefreshResponse,
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
        refresh_token_exp_minutes=10,
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
        authorization: str | None = Header(None),
        token_manager: TokenManager = Depends(lambda: test_token_manager),
    ) -> uuid.UUID:
        if not authorization or not authorization.startswith("Bearer "):
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


# Helper to check datetime strings
def is_iso_datetime_z(dt_str: str) -> bool:
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.tzinfo == timezone.utc
    except (ValueError, TypeError):
        return False


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
    response_data = response.json()
    assert response_data["username"] == sample_profile_data["username"]
    assert response_data["name"] == sample_profile_data["name"]
    # Check Profile response types and format
    assert isinstance(response_data["id"], str)
    try:
        uuid.UUID(response_data["id"])
    except ValueError:
        pytest.fail(f"Invalid UUID format for id: {response_data['id']}")
    assert isinstance(response_data["created_at"], str)
    assert is_iso_datetime_z(response_data["created_at"])
    assert isinstance(response_data["updated_at"], str)
    assert is_iso_datetime_z(response_data["updated_at"])
    assert isinstance(response_data["password_updated_at"], str)
    assert is_iso_datetime_z(response_data["password_updated_at"])

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
    # Test cases hitting boundaries
    valid_min_user = "abc"
    valid_min_pass = "abcdefgh"
    valid_min_name = "def"
    invalid_short_user = "ab"
    invalid_short_pass = "abcdefg"
    invalid_short_name = "de"
    # Potentially add tests for max length if needed
    # valid_max_user = "a" * 20
    # invalid_long_user = "a" * 21

    test_cases = [
        ({"username": invalid_short_user, "password": valid_min_pass, "name": valid_min_name}, 422),
        ({"username": valid_min_user, "password": invalid_short_pass, "name": valid_min_name}, 422),
        ({"username": valid_min_user, "password": valid_min_pass, "name": invalid_short_name}, 422),
        # Original test case
        ({"username": "us", "password": "pass", "name": "Te"}, 422),
    ]

    for payload, expected_status in test_cases:
        response = client.post("/api/auth/register", json=payload)
        assert response.status_code == expected_status


def test_login_success(client: TestClient, mock_user_service: AsyncMock):
    login_response_data = {
        "access_token": "fake_access_token",
        "refresh_token": "fake_refresh_token",
    }
    mock_user_service.login.return_value = LoginResponse(**login_response_data)
    login_payload = {"username": "testuser", "password": "password123"}
    response = client.post("/api/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data == login_response_data
    # Check LoginResponse types
    assert isinstance(response_data["access_token"], str)
    assert isinstance(response_data["refresh_token"], str)
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
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.post("/api/auth/validate", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b""


def test_validate_token_no_header(client: TestClient, override_dependencies):
    response = client.post("/api/auth/validate")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_validate_token_invalid_scheme(
    client: TestClient, override_dependencies
):
    headers = {"Authorization": "Basic invalid"}
    response = client.post("/api/auth/validate", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_refresh_token_success(
    client: TestClient, mock_user_service: AsyncMock
):
    refresh_response_data = {"access_token": "new_fake_access_token"}
    mock_user_service.refresh.return_value = RefreshResponse(
        **refresh_response_data
    )
    refresh_payload = {"refresh_token": "valid_refresh_token"}
    response = client.post("/api/auth/refresh", json=refresh_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == refresh_response_data
    mock_user_service.refresh.assert_awaited_once()


def test_refresh_token_unauthorized(
    client: TestClient, mock_user_service: AsyncMock
):
    mock_user_service.refresh.side_effect = InvalidOrExpiredRefreshToken()
    refresh_payload = {"refresh_token": "invalid_or_expired_token"}
    response = client.post("/api/auth/refresh", json=refresh_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired refresh token"}


def test_get_profile_success(
    client: TestClient,
    mock_user_service: AsyncMock,
    sample_profile_data,
    override_dependencies,
):
    user_id = override_dependencies
    mock_user_service.get_profile.return_value = Profile(**sample_profile_data)
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.get("/api/auth/profile", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    # Check Profile response types and format
    assert isinstance(response_data["id"], str)
    try:
        uuid.UUID(response_data["id"])
    except ValueError:
        pytest.fail(f"Invalid UUID format for id: {response_data['id']}")
    assert isinstance(response_data["username"], str)
    assert isinstance(response_data["name"], str)
    assert isinstance(response_data["created_at"], str)
    assert is_iso_datetime_z(response_data["created_at"])
    assert isinstance(response_data["updated_at"], str)
    assert is_iso_datetime_z(response_data["updated_at"])
    assert isinstance(response_data["password_updated_at"], str)
    assert is_iso_datetime_z(response_data["password_updated_at"])

    # Compare main values
    assert response_data["id"] == sample_profile_data["id"]
    assert response_data["username"] == sample_profile_data["username"]
    assert response_data["name"] == sample_profile_data["name"]

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
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.put(
        "/api/auth/password", json=password_payload, headers=headers
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
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.put(
        "/api/auth/password", json=password_payload, headers=headers
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect old password"}
    mock_user_service.change_password.assert_awaited_once()


def test_change_password_validation_error(
    client: TestClient, override_dependencies
):
    password_payload = {
        "old_password": "ValidOld1",
        "new_password": "short",
    }
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.put(
        "/api/auth/password", json=password_payload, headers=headers
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
    new_name = "New Name"
    updated_profile_data["name"] = new_name
    expected_profile = Profile(**updated_profile_data)
    mock_user_service.update_profile.return_value = expected_profile

    profile_payload = {"name": new_name}
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.put(
        "/api/auth/profile", json=profile_payload, headers=headers
    )

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(expected_profile.id)
    assert response_data["username"] == expected_profile.username
    assert response_data["name"] == expected_profile.name
    assert response_data["updated_at"] == expected_profile.updated_at.isoformat().replace("+00:00", "Z")
    assert response_data["created_at"] == expected_profile.created_at.isoformat().replace("+00:00", "Z")
    assert response_data["password_updated_at"] == expected_profile.password_updated_at.isoformat().replace("+00:00", "Z")

    mock_user_service.update_profile.assert_awaited_once()
    call_args = mock_user_service.update_profile.call_args[0]
    assert call_args[0] == user_id
    assert call_args[1].name == new_name


def test_update_profile_validation_error(
    client: TestClient, override_dependencies
):
    profile_payload = {"name": "N"}
    headers = {"Authorization": "Bearer valid.token.for.test"}
    response = client.put(
        "/api/auth/profile", json=profile_payload, headers=headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_update_profile_unauthorized(client: TestClient, override_dependencies):
    update_payload = {"name": "Updated Name"}
    response = client.put("/api/auth/profile", json=update_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


# Add test for login validation errors
def test_login_validation_error(client: TestClient):
    # Test cases hitting boundaries
    valid_min_user = "usr"
    valid_min_pass = "securep1"
    invalid_short_user = "us"
    invalid_short_pass = "secure7"
    # Potentially add tests for max length

    test_cases = [
        ({"username": invalid_short_user, "password": valid_min_pass}, 422),
        ({"username": valid_min_user, "password": invalid_short_pass}, 422),
    ]

    for payload, expected_status in test_cases:
        response = client.post("/api/auth/login", json=payload)
        assert response.status_code == expected_status
