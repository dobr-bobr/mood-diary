import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import Cookie, status
from fastapi.testclient import TestClient

from mood_diary.backend.config import Settings
from mood_diary.backend.exceptions.user import (
    IncorrectOldPassword,
    IncorrectPasswordOrUserDoesNotExists,
    InvalidOrExpiredAccessToken,
    UsernameAlreadyExists,
)
from mood_diary.backend.app import get_app
from mood_diary.backend.routes.dependencies import (
    get_token_manager,
    get_user_service,
    get_current_user_id,
)
from mood_diary.backend.database.cache import get_redis_client
from mood_diary.backend.services.user import UserService
from mood_diary.backend.utils.token_manager import (
    JWTTokenManager,
    TokenManager,
    TokenType,
)
from mood_diary.common.api.schemas.auth import (
    LoginResponse,
    Profile,
    RegisterRequest,
    ChangePasswordRequest,
)


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    mock_redis.set.return_value = None
    mock_redis.delete.return_value = None

    async def mock_scan_iter(*args, **kwargs):
        if False:
            yield
        return

    mock_redis.scan_iter = mock_scan_iter
    return mock_redis


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
    test_settings = Settings(
        AUTH_TOKEN_SECRET_KEY="fixed-test-secret-key",
        SQLITE_DB_PATH=":memory:",
        REDIS_HOST="mocked_redis",
        CSRF_SECRET_KEY="fixed-test-csrf-secret-key",
    )
    app = get_app(test_settings)
    yield app


@pytest.fixture
def override_dependencies(
    mock_user_service: AsyncMock,
    test_token_manager: TokenManager,
    main_app,
    mock_redis_client: AsyncMock,
):
    test_user_id = uuid.uuid4()

    async def mock_get_current_user_id_simple_check(
        access_token: str | None = Cookie(None),
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
    main_app.dependency_overrides[get_redis_client] = lambda: mock_redis_client

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
    test_user_id_for_data = uuid.uuid4()
    return {
        "id": str(test_user_id_for_data),
        "username": "testuser",
        "name": "Test User",
        "created_at": now_iso,
        "updated_at": now_iso,
        "password_updated_at": now_iso,
    }


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
    assert isinstance(response_data["id"], str)
    assert response_data["id"] == sample_profile_data["id"]
    try:
        uuid.UUID(response_data["id"])
    except ValueError:
        pytest.fail(f"Invalid UUID format for id: {response_data['id']}")
    assert isinstance(response_data["created_at"], str)
    assert is_iso_datetime_z(response_data["created_at"])
    assert response_data["created_at"] == sample_profile_data["created_at"]
    assert isinstance(response_data["updated_at"], str)
    assert is_iso_datetime_z(response_data["updated_at"])
    assert response_data["updated_at"] == sample_profile_data["updated_at"]
    assert isinstance(response_data["password_updated_at"], str)
    assert is_iso_datetime_z(response_data["password_updated_at"])
    assert (
        response_data["password_updated_at"]
        == sample_profile_data["password_updated_at"]
    )

    mock_user_service.register.assert_awaited_once()


def test_register_success_boundaries(
    client: TestClient, mock_user_service: AsyncMock, sample_profile_data
):
    """Tests successful registration with boundary length inputs."""
    test_user_id = uuid.uuid4()  # Use a fixed UUID for mock consistency
    base_profile = sample_profile_data.copy()
    base_profile["id"] = str(test_user_id)

    # Test cases with exact min/max lengths
    min_user = "u" * 3
    max_user = "u" * 20
    min_pass = "p" * 8
    max_pass = "p" * 32
    min_name = "n" * 3
    max_name = "n" * 32

    test_cases = [
        # Min boundaries
        {"username": min_user, "password": min_pass, "name": min_name},
        # Max boundaries
        {"username": max_user, "password": max_pass, "name": max_name},
        # Mix min/max
        {"username": min_user, "password": max_pass, "name": min_name},
        {"username": max_user, "password": min_pass, "name": max_name},
    ]

    for payload in test_cases:
        # Ensure the mock is reset and configured for each case
        mock_user_service.reset_mock()
        # Adapt profile data to match request (username, name)
        profile_data = base_profile.copy()
        profile_data["username"] = payload["username"]
        profile_data["name"] = payload["name"]
        mock_user_service.register.return_value = Profile(**profile_data)

        response = client.post("/api/auth/register", json=payload)

        assert response.status_code == status.HTTP_200_OK
        # Basic check that registration seems to have worked
        response_data = response.json()
        assert response_data["username"] == payload["username"]
        assert response_data["name"] == payload["name"]
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
    mock_user_service.register.assert_awaited_once()
    # Check arguments passed to the service
    call_args = mock_user_service.register.call_args[0]
    assert isinstance(call_args[0], RegisterRequest)
    assert call_args[0].username == register_payload["username"]
    assert call_args[0].password == register_payload["password"]
    assert call_args[0].name == register_payload["name"]
    # Ensure the correct exception was raised by the mock
    assert isinstance(
        mock_user_service.register.side_effect, UsernameAlreadyExists
    )


def test_register_validation_error(client: TestClient):
    # Min lengths
    valid_min_user = "u" * 3
    valid_min_pass = "p" * 8
    valid_min_name = "n" * 3
    # Max lengths
    valid_max_user = "u" * 20
    valid_max_pass = "p" * 32
    valid_max_name = "n" * 32

    # Invalid lengths
    invalid_short_user = "u" * (3 - 1)
    invalid_short_pass = "p" * (8 - 1)
    invalid_short_name = "n" * (3 - 1)
    invalid_long_user = "u" * (20 + 1)
    invalid_long_pass = "p" * (32 + 1)
    invalid_long_name = "n" * (32 + 1)

    test_cases = [
        # Too short
        (
            {
                "username": invalid_short_user,
                "password": valid_min_pass,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": invalid_short_pass,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": valid_min_pass,
                "name": invalid_short_name,
            },
            422,
        ),
        # Too long
        (
            {
                "username": invalid_long_user,
                "password": valid_min_pass,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": invalid_long_pass,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": valid_min_pass,
                "name": invalid_long_name,
            },
            422,
        ),
        # Missing fields
        (
            {"password": valid_min_pass, "name": valid_min_name},
            422,
        ),  # Missing username
        (
            {"username": valid_min_user, "name": valid_min_name},
            422,
        ),  # Missing password
        (
            {"username": valid_min_user, "password": valid_min_pass},
            422,
        ),  # Missing name
        ({}, 422),  # Missing all
        # Null fields
        (
            {
                "username": None,
                "password": valid_min_pass,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": None,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": valid_min_pass,
                "name": None,
            },
            422,
        ),
        # Wrong types
        (
            {
                "username": 123,
                "password": valid_min_pass,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": 123,
                "name": valid_min_name,
            },
            422,
        ),
        (
            {
                "username": valid_min_user,
                "password": valid_min_pass,
                "name": 123,
            },
            422,
        ),
    ]

    for payload, expected_status in test_cases:
        response = client.post("/api/auth/register", json=payload)
        assert (
            response.status_code == expected_status
        ), f"Failed for payload: {payload}"


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
    test_token_manager: JWTTokenManager,
):
    """Tests successfully retrieving the user profile."""
    fixed_user_id = override_dependencies
    profile_data = sample_profile_data.copy()
    profile_data["id"] = str(fixed_user_id)
    expected_profile = Profile(**profile_data)

    mock_user_service.get_profile.return_value = expected_profile
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.get("/api/auth/profile")
    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert isinstance(response_data["id"], str)
    assert response_data["id"] == str(fixed_user_id)
    try:
        uuid.UUID(response_data["id"])
    except ValueError:
        pytest.fail(f"Invalid UUID format for id: {response_data['id']}")
    assert isinstance(response_data["username"], str)
    assert response_data["username"] == sample_profile_data["username"]
    assert isinstance(response_data["name"], str)
    assert response_data["name"] == sample_profile_data["name"]
    assert isinstance(response_data["created_at"], str)
    assert is_iso_datetime_z(response_data["created_at"])
    assert response_data["created_at"] == sample_profile_data["created_at"]
    assert isinstance(response_data["updated_at"], str)
    assert is_iso_datetime_z(response_data["updated_at"])
    assert response_data["updated_at"] == sample_profile_data["updated_at"]
    assert isinstance(response_data["password_updated_at"], str)
    assert is_iso_datetime_z(response_data["password_updated_at"])
    assert (
        response_data["password_updated_at"]
        == sample_profile_data["password_updated_at"]
    )

    # Compare main values
    assert response_data["id"] == str(fixed_user_id)
    assert response_data["username"] == sample_profile_data["username"]
    assert response_data["name"] == sample_profile_data["name"]

    mock_user_service.get_profile.assert_awaited_once_with(fixed_user_id)


def test_get_profile_unauthorized(client: TestClient, override_dependencies):
    response = client.get("/api/auth/profile")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_update_profile_success(
    client: TestClient,
    mock_user_service: AsyncMock,
    sample_profile_data,
    override_dependencies,
    test_token_manager: JWTTokenManager,
):
    # Extract user ID from sample data
    user_id = uuid.UUID(sample_profile_data["id"])
    updated_profile_data = sample_profile_data.copy()
    new_name = "New Name"
    updated_profile_data["name"] = new_name
    expected_profile = Profile(**updated_profile_data)
    mock_user_service.update_profile.return_value = expected_profile

    profile_payload = {"name": new_name}
    # Create a valid access token
    access_token = test_token_manager.create_token(
        token_type=TokenType.ACCESS, user_id=user_id
    )
    client.cookies.set("access_token", access_token)

    response = client.put("/api/auth/profile", json=profile_payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["id"] == str(expected_profile.id)
    assert response_data["username"] == expected_profile.username
    assert response_data["name"] == expected_profile.name
    assert response_data[
        "updated_at"
    ] == expected_profile.updated_at.isoformat().replace("+00:00", "Z")
    assert response_data[
        "created_at"
    ] == expected_profile.created_at.isoformat().replace("+00:00", "Z")
    assert response_data[
        "password_updated_at"
    ] == expected_profile.password_updated_at.isoformat().replace(
        "+00:00", "Z"
    )
    # Verify all fields match the expected Profile schema returned by the mock service
    assert response_data == expected_profile.model_dump(mode="json")

    mock_user_service.update_profile.assert_awaited_once()
    call_args = mock_user_service.update_profile.call_args[0]
    assert (
        call_args[0] == override_dependencies
    )  # Use fixed_user_id from override_dependencies


def test_update_profile_success_boundaries(
    client: TestClient,
    mock_user_service: AsyncMock,
    sample_profile_data,
    override_dependencies,
    test_token_manager: JWTTokenManager,
):
    # Extract user ID from sample data
    user_id = uuid.UUID(sample_profile_data["id"])
    base_profile = sample_profile_data.copy()
    # base_profile["id"] = str(user_id) # Already set in sample_profile_data

    # Min/Max lengths
    min_name = "n" * 3
    max_name = "n" * 32

    test_cases = [
        {"name": min_name},
        {"name": max_name},
    ]

    for payload in test_cases:
        mock_user_service.reset_mock()
        # Adapt profile data to match request
        profile_data = base_profile.copy()
        profile_data["name"] = payload["name"]
        # Ensure updated_at is handled if mock needs it
        profile_data["updated_at"] = datetime.now(timezone.utc)
        mock_user_service.update_profile.return_value = Profile(**profile_data)

        # Create a valid access token for each case
        access_token = test_token_manager.create_token(
            token_type=TokenType.ACCESS, user_id=user_id
        )
        client.cookies.set("access_token", access_token)

        response = client.put("/api/auth/profile", json=payload)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["name"] == payload["name"]  # Check name updated
        mock_user_service.update_profile.assert_awaited_once()


def test_update_profile_validation_error(
    client: TestClient,
    override_dependencies,
    test_token_manager: JWTTokenManager,
):
    # Min/Max lengths
    min_name = "n" * 3
    max_name = "n" * 32

    # Invalid lengths
    invalid_short_name = "n" * (3 - 1)
    invalid_long_name = "n" * (32 + 1)

    # Create a valid token once, needed for authorization
    access_token = test_token_manager.create_token(
        token_type=TokenType.ACCESS, user_id=uuid.uuid4()
    )  # Pass UUID directly
    client.cookies.set("access_token", access_token)

    test_cases = [
        # Name too short
        ({"name": invalid_short_name}, 422),
        # Name too long
        ({"name": invalid_long_name}, 422),
        # Original case (name too short)
        ({"name": "N"}, 422),
        # Missing field - Note: PUT requires the field, so this becomes 422
        ({}, 422),  # FastAPI should catch missing 'name'
        # Null field
        ({"name": None}, 422),
        # Wrong type
        ({"name": 123}, 422),
    ]

    for payload, expected_status in test_cases:
        response = client.put("/api/auth/profile", json=payload)
        assert (
            response.status_code == expected_status
        ), f"Failed for payload: {payload}"


def test_update_profile_unauthorized(
    client: TestClient, override_dependencies
):
    update_payload = {"name": "Updated Name"}
    response = client.put("/api/auth/profile", json=update_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Invalid or expired access token"}


def test_login_validation_error(client: TestClient):
    # Min/Max lengths
    valid_min_user = "u" * 3
    valid_min_pass = "p" * 8
    valid_max_user = "u" * 20
    valid_max_pass = "p" * 32

    # Invalid lengths
    invalid_short_user = "u" * (3 - 1)
    invalid_short_pass = "p" * (8 - 1)
    invalid_long_user = "u" * (20 + 1)
    invalid_long_pass = "p" * (32 + 1)

    test_cases = [
        # Too short
        ({"username": invalid_short_user, "password": valid_min_pass}, 422),
        ({"username": valid_min_user, "password": invalid_short_pass}, 422),
        # Too long
        ({"username": invalid_long_user, "password": valid_min_pass}, 422),
        ({"username": valid_min_user, "password": invalid_long_pass}, 422),
        # Missing fields
        ({"password": valid_min_pass}, 422),  # Missing username
        ({"username": valid_min_user}, 422),  # Missing password
        ({}, 422),  # Missing all
        # Null fields
        ({"username": None, "password": valid_min_pass}, 422),
        ({"username": valid_min_user, "password": None}, 422),
        # Wrong types
        ({"username": 123, "password": valid_min_pass}, 422),
        ({"username": valid_min_user, "password": 123}, 422),
    ]

    for payload, expected_status in test_cases:
        response = client.post("/api/auth/login", json=payload)
        assert (
            response.status_code == expected_status
        ), f"Failed for payload: {payload}"


def test_change_password_success(
    client: TestClient,
    mock_user_service: AsyncMock,
    override_dependencies,
    test_token_manager: JWTTokenManager,
):
    """Tests successfully changing the password."""
    # Get the user_id yielded by the override_dependencies fixture
    fixed_user_id = override_dependencies
    mock_user_service.change_password.return_value = None
    password_payload = {
        "old_password": "oldPass123",
        "new_password": "newPass456!",
    }
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put("/api/auth/password", json=password_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.content == b""
    mock_user_service.change_password.assert_awaited_once()
    call_args = mock_user_service.change_password.call_args[0]
    assert (
        call_args[0] == fixed_user_id
    )  # Assert with the user_id from the override
    assert isinstance(call_args[1], ChangePasswordRequest)  # Check type
    assert call_args[1].old_password == "oldPass123"
    assert call_args[1].new_password == "newPass456!"


def test_change_password_success_boundaries(
    client: TestClient,
    mock_user_service: AsyncMock,
    override_dependencies,
    test_token_manager: JWTTokenManager,
):
    # Create dummy user ID
    user_id = uuid.uuid4()
    # Create a valid token
    access_token = test_token_manager.create_token(
        token_type=TokenType.ACCESS, user_id=user_id
    )
    client.cookies.set("access_token", access_token)

    # Min/Max lengths
    min_pass = "p" * 8
    max_pass = "p" * 32

    test_cases = [
        # Min boundaries
        {"old_password": min_pass, "new_password": min_pass},
        # Max boundaries
        {"old_password": max_pass, "new_password": max_pass},
        # Mix min/max
        {"old_password": min_pass, "new_password": max_pass},
        {"old_password": max_pass, "new_password": min_pass},
    ]

    for payload in test_cases:
        mock_user_service.reset_mock()
        mock_user_service.change_password.return_value = (
            None  # Success returns None
        )

        response = client.put("/api/auth/password", json=payload)

        assert response.status_code == status.HTTP_200_OK
        assert response.content == b""  # Check for empty byte string response

        mock_user_service.change_password.assert_awaited_once_with(
            override_dependencies,  # Ensure correct user ID is asserted
            ChangePasswordRequest(**payload),
        )


def test_change_password_incorrect_old(
    client: TestClient,
    mock_user_service: AsyncMock,
    override_dependencies,
    test_token_manager: JWTTokenManager,
):
    """Tests password change failure due to incorrect old password."""
    # Get the user_id yielded by the override_dependencies fixture
    fixed_user_id = override_dependencies
    mock_user_service.change_password.side_effect = IncorrectOldPassword()
    password_payload = {
        "old_password": "wrongOldPass",
        "new_password": "newPass456!",
    }
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put("/api/auth/password", json=password_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Incorrect old password"}
    mock_user_service.change_password.assert_awaited_once()
    # Check arguments passed to the service
    call_args = mock_user_service.change_password.call_args[0]
    assert call_args[0] == fixed_user_id  # Check user_id from override
    assert isinstance(call_args[1], ChangePasswordRequest)
    assert call_args[1].old_password == password_payload["old_password"]
    assert call_args[1].new_password == password_payload["new_password"]
    # Ensure the correct exception was raised by the mock
    assert isinstance(
        mock_user_service.change_password.side_effect, IncorrectOldPassword
    )


def test_change_password_validation_error(
    client: TestClient, override_dependencies
):
    password_payload = {
        "old_password": "ValidOld1",
        "new_password": "short",
    }
    client.cookies.set("access_token", "valid.token.for.test")
    response = client.put("/api/auth/password", json=password_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
