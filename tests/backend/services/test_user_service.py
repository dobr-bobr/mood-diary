import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from mood_diary.backend.exceptions.user import (
    IncorrectOldPassword,
    IncorrectPasswordOrUserDoesNotExists,
    InvalidOrExpiredRefreshToken,
    UsernameAlreadyExists,
    UserNotFound,
)
from mood_diary.backend.repositories.sсhemas.user import (
    User as UserSchema,
)
from mood_diary.backend.services.user import UserService
from mood_diary.backend.utils.token_manager import (
    TokenPayload,
    TokenType,
)
from mood_diary.common.api.schemas.auth import (
    ChangePasswordRequest,
    ChangeProfileRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
)


@pytest.fixture
def mock_user_repository():
    return AsyncMock()


@pytest.fixture
def mock_password_hasher():
    mock = Mock()
    mock.hash.return_value = "hashed_password"
    mock.verify.return_value = True
    return mock


@pytest.fixture
def mock_token_manager():
    mock = Mock()
    mock.create_token.side_effect = lambda type, uid: f"{type.value}-{uid}"
    mock.decode_token.return_value = TokenPayload(
        type=TokenType.REFRESH,
        user_id=uuid.uuid4(),
        iat=int(datetime.now(timezone.utc).timestamp()),
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
    )
    return mock


@pytest.fixture
def user_service(
    mock_user_repository,
    mock_password_hasher,
    mock_token_manager,
):
    return UserService(
        user_repository=mock_user_repository,
        password_hasher=mock_password_hasher,
        token_manager=mock_token_manager,
    )


@pytest.fixture
def sample_user():
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    return UserSchema(
        id=user_id,
        username="testuser",
        hashed_password="hashed_password",
        name="Test User",
        created_at=now,
        updated_at=now,
        password_updated_at=now,
    )


# --- Register Tests ---


@pytest.mark.asyncio
async def test_register_success(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
    sample_user: UserSchema,
):
    mock_user_repository.create.return_value = sample_user
    register_request = RegisterRequest(
        username="testuser", password="password123", name="Test User"
    )

    profile = await user_service.register(register_request)

    mock_password_hasher.hash.assert_called_once_with("password123")
    mock_user_repository.create.assert_awaited_once()
    assert profile.id == sample_user.id
    assert profile.username == sample_user.username
    assert profile.name == sample_user.name


@pytest.mark.asyncio
async def test_register_username_exists(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
):
    mock_user_repository.create.return_value = None  # Simulate username exists
    register_request = RegisterRequest(
        username="existinguser", password="password123", name="Test User"
    )

    with pytest.raises(UsernameAlreadyExists):
        await user_service.register(register_request)

    mock_password_hasher.hash.assert_called_once_with("password123")
    mock_user_repository.create.assert_awaited_once()


# --- Login Tests ---


@pytest.mark.asyncio
async def test_login_success(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
    mock_token_manager: Mock,
    sample_user: UserSchema,
):
    mock_user_repository.get_by_username.return_value = sample_user
    login_request = LoginRequest(username="testuser", password="password123")

    response = await user_service.login(login_request)

    mock_user_repository.get_by_username.assert_awaited_once_with("testuser")
    mock_password_hasher.verify.assert_called_once_with(
        "password123", "hashed_password"
    )
    mock_token_manager.create_token.assert_any_call(
        TokenType.ACCESS, sample_user.id
    )
    mock_token_manager.create_token.assert_any_call(
        TokenType.REFRESH, sample_user.id
    )
    assert response.access_token == f"ACCESS-{sample_user.id}"
    assert response.refresh_token == f"REFRESH-{sample_user.id}"


@pytest.mark.asyncio
async def test_login_user_not_found(
    user_service: UserService, mock_user_repository: AsyncMock
):
    mock_user_repository.get_by_username.return_value = None
    login_request = LoginRequest(
        username="unknownuser", password="password123"
    )

    with pytest.raises(IncorrectPasswordOrUserDoesNotExists):
        await user_service.login(login_request)

    mock_user_repository.get_by_username.assert_awaited_once_with(
        "unknownuser"
    )


@pytest.mark.asyncio
async def test_login_incorrect_password(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
    sample_user: UserSchema,
):
    mock_user_repository.get_by_username.return_value = sample_user
    mock_password_hasher.verify.return_value = (
        False  # Simulate incorrect password
    )
    login_request = LoginRequest(username="testuser", password="wrongpassword")

    with pytest.raises(IncorrectPasswordOrUserDoesNotExists):
        await user_service.login(login_request)

    mock_user_repository.get_by_username.assert_awaited_once_with("testuser")
    mock_password_hasher.verify.assert_called_once_with(
        "wrongpassword", "hashed_password"
    )


# --- Refresh Tests ---


@pytest.mark.asyncio
async def test_refresh_success(
    user_service: UserService, mock_token_manager: Mock
):
    refresh_token = "valid_refresh_token"
    refresh_request = RefreshRequest(refresh_token=refresh_token)
    decoded_payload = TokenPayload(
        type=TokenType.REFRESH,
        user_id=uuid.uuid4(),
        iat=int(datetime.now(timezone.utc).timestamp()),
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
    )
    mock_token_manager.decode_token.return_value = decoded_payload

    response = await user_service.refresh(refresh_request)

    mock_token_manager.decode_token.assert_called_once_with(refresh_token)
    mock_token_manager.create_token.assert_called_once_with(
        TokenType.ACCESS, decoded_payload.user_id
    )
    assert response.access_token == f"ACCESS-{decoded_payload.user_id}"


@pytest.mark.asyncio
async def test_refresh_invalid_token(
    user_service: UserService, mock_token_manager: Mock
):
    refresh_token = "invalid_token"
    refresh_request = RefreshRequest(refresh_token=refresh_token)
    mock_token_manager.decode_token.return_value = (
        None  # Simulate invalid token
    )

    with pytest.raises(InvalidOrExpiredRefreshToken):
        await user_service.refresh(refresh_request)

    mock_token_manager.decode_token.assert_called_once_with(refresh_token)


@pytest.mark.asyncio
async def test_refresh_wrong_token_type(
    user_service: UserService, mock_token_manager: Mock
):
    refresh_token = "access_token_instead"
    refresh_request = RefreshRequest(refresh_token=refresh_token)
    # Simulate decoding an access token instead of a refresh token
    decoded_payload = TokenPayload(
        type=TokenType.ACCESS,
        user_id=uuid.uuid4(),
        iat=int(datetime.now(timezone.utc).timestamp()),
        exp=int(datetime.now(timezone.utc).timestamp()) + 3600,
    )
    mock_token_manager.decode_token.return_value = decoded_payload

    with pytest.raises(InvalidOrExpiredRefreshToken):
        await user_service.refresh(refresh_request)

    mock_token_manager.decode_token.assert_called_once_with(refresh_token)


# --- Get Profile Tests ---


@pytest.mark.asyncio
async def test_get_profile_success(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    sample_user: UserSchema,
):
    mock_user_repository.get.return_value = sample_user

    profile = await user_service.get_profile(sample_user.id)

    mock_user_repository.get.assert_awaited_once_with(sample_user.id)
    assert profile.id == sample_user.id
    assert profile.username == sample_user.username
    assert profile.name == sample_user.name


@pytest.mark.asyncio
async def test_get_profile_not_found(
    user_service: UserService, mock_user_repository: AsyncMock
):
    unknown_user_id = uuid.uuid4()
    mock_user_repository.get.return_value = None

    with pytest.raises(UserNotFound):
        await user_service.get_profile(unknown_user_id)

    mock_user_repository.get.assert_awaited_once_with(unknown_user_id)


# --- Change Password Tests ---


@pytest.mark.asyncio
async def test_change_password_success(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
    sample_user: UserSchema,
):
    mock_user_repository.get.return_value = sample_user
    mock_user_repository.update_hashed_password.return_value = sample_user
    change_password_request = ChangePasswordRequest(
        old_password="password123", new_password="newStrongPassword1!"
    )

    await user_service.change_password(sample_user.id, change_password_request)

    mock_user_repository.get.assert_awaited_once_with(sample_user.id)
    mock_password_hasher.verify.assert_called_once_with(
        "password123", sample_user.hashed_password
    )
    mock_password_hasher.hash.assert_called_once_with("newStrongPassword1!")
    mock_user_repository.update_hashed_password.assert_awaited_once()
    # Check if the correct arguments were passed to update_hashed_password
    call_args = mock_user_repository.update_hashed_password.call_args[0]
    assert call_args[0] == sample_user.id
    assert (
        call_args[1].hashed_password == "hashed_password"
    )  # From mock_password_hasher.hash


@pytest.mark.asyncio
async def test_change_password_user_not_found(
    user_service: UserService, mock_user_repository: AsyncMock
):
    unknown_user_id = uuid.uuid4()
    mock_user_repository.get.return_value = None
    change_password_request = ChangePasswordRequest(
        old_password="password123", new_password="newStrongPassword1!"
    )

    with pytest.raises(UserNotFound):
        await user_service.change_password(
            unknown_user_id, change_password_request
        )

    mock_user_repository.get.assert_awaited_once_with(unknown_user_id)
    mock_user_repository.update_hashed_password.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password_incorrect_old_password(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
    sample_user: UserSchema,
):
    mock_user_repository.get.return_value = sample_user
    mock_password_hasher.verify.return_value = (
        False  # Simulate incorrect old password
    )
    change_password_request = ChangePasswordRequest(
        old_password="wrongoldpassword", new_password="newStrongPassword1!"
    )

    with pytest.raises(IncorrectOldPassword):
        await user_service.change_password(
            sample_user.id, change_password_request
        )

    mock_user_repository.get.assert_awaited_once_with(sample_user.id)
    mock_password_hasher.verify.assert_called_once_with(
        "wrongoldpassword", sample_user.hashed_password
    )
    mock_user_repository.update_hashed_password.assert_not_awaited()


@pytest.mark.asyncio
async def test_change_password_update_fails(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    mock_password_hasher: Mock,
    sample_user: UserSchema,
):
    mock_user_repository.get.return_value = sample_user
    mock_user_repository.update_hashed_password.return_value = (
        None  # Simulate update failure
    )
    change_password_request = ChangePasswordRequest(
        old_password="password123", new_password="newStrongPassword1!"
    )

    with pytest.raises(
        UserNotFound
    ):  # Or maybe a different exception? Assuming UserNotFound based on code
        await user_service.change_password(
            sample_user.id, change_password_request
        )

    mock_user_repository.get.assert_awaited_once_with(sample_user.id)
    mock_password_hasher.verify.assert_called_once_with(
        "password123", sample_user.hashed_password
    )
    mock_password_hasher.hash.assert_called_once_with("newStrongPassword1!")
    mock_user_repository.update_hashed_password.assert_awaited_once()


# --- Update Profile Tests ---


@pytest.mark.asyncio
async def test_update_profile_success(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    sample_user: UserSchema,
):
    mock_user_repository.get.return_value = sample_user
    updated_user = sample_user.model_copy()
    updated_user.name = "New Test Name"
    updated_user.updated_at = datetime.now(timezone.utc)
    mock_user_repository.update_profile.return_value = updated_user

    change_profile_request = ChangeProfileRequest(name="New Test Name")

    profile = await user_service.update_profile(
        sample_user.id, change_profile_request
    )

    mock_user_repository.get.assert_awaited_once_with(sample_user.id)
    mock_user_repository.update_profile.assert_awaited_once()
    # Check if the correct arguments were passed to update_profile
    call_args = mock_user_repository.update_profile.call_args[0]
    assert call_args[0] == sample_user.id
    assert call_args[1].name == "New Test Name"

    assert profile.id == updated_user.id
    assert profile.username == updated_user.username
    assert profile.name == "New Test Name"
    assert profile.updated_at == updated_user.updated_at


@pytest.mark.asyncio
async def test_update_profile_user_not_found(
    user_service: UserService, mock_user_repository: AsyncMock
):
    unknown_user_id = uuid.uuid4()
    mock_user_repository.get.return_value = None
    change_profile_request = ChangeProfileRequest(name="New Name")

    with pytest.raises(UserNotFound):
        await user_service.update_profile(
            unknown_user_id, change_profile_request
        )

    mock_user_repository.get.assert_awaited_once_with(unknown_user_id)
    mock_user_repository.update_profile.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_profile_update_fails(
    user_service: UserService,
    mock_user_repository: AsyncMock,
    sample_user: UserSchema,
):
    mock_user_repository.get.return_value = sample_user
    mock_user_repository.update_profile.return_value = (
        None  # Simulate update failure
    )
    change_profile_request = ChangeProfileRequest(name="New Name")

    with pytest.raises(UserNotFound):
        await user_service.update_profile(
            sample_user.id, change_profile_request
        )

    mock_user_repository.get.assert_awaited_once_with(sample_user.id)
    mock_user_repository.update_profile.assert_awaited_once()
