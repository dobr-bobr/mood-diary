import sqlite3
import uuid
from datetime import datetime, timezone
from unittest.mock import ANY, AsyncMock, MagicMock, patch, Mock

import pytest

from mood_diary.backend.repositories.sqlite.user import SQLiteUserRepository
from mood_diary.backend.repositories.sсhemas.user import (
    CreateUser,
    UpdateUserHashedPassword,
    UpdateUserProfile,
    User,
)


# --- Fixtures ---


@pytest.fixture
def user_repo(mock_connection):
    repo = SQLiteUserRepository(mock_connection)
    repo.get = AsyncMock(spec=repo.get)
    repo.get_by_username = AsyncMock(spec=repo.get_by_username)
    return repo


@pytest.fixture
def sample_user_data():
    user_id = uuid.uuid4()
    now = datetime.now()
    return (
        str(user_id),
        "testuser",
        "Test User",
        "hashed_password",
        now,
        now,
        now,
    )


@pytest.fixture
def sample_user_schema(sample_user_data):
    return User(
        id=uuid.UUID(sample_user_data[0]),
        username=sample_user_data[1],
        name=sample_user_data[2],
        hashed_password=sample_user_data[3],
        created_at=sample_user_data[4],
        updated_at=sample_user_data[5],
        password_updated_at=sample_user_data[6],
    )


# --- Test Cases ---


def test_init_db(
    user_repo: SQLiteUserRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_repo.init_db()
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(ANY)
    assert (
        "CREATE TABLE IF NOT EXISTS users"
        in mock_cursor.execute.call_args[0][0]
    )
    mock_connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_found(
    user_repo: SQLiteUserRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_user_data: tuple,
    sample_user_schema: User,
):
    user_id = sample_user_schema.id
    mock_cursor.fetchone.return_value = sample_user_data

    real_repo = SQLiteUserRepository(mock_connection)
    user = await real_repo.get(user_id)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE id = ?", (str(user_id),)
    )
    mock_cursor.fetchone.assert_called_once()
    assert user is not None
    assert user.id == sample_user_schema.id
    assert user.username == sample_user_schema.username
    assert user.name == sample_user_schema.name
    assert user.hashed_password == sample_user_schema.hashed_password
    assert user.created_at.replace(
        tzinfo=None
    ) == sample_user_schema.created_at.replace(tzinfo=None)
    assert user.updated_at.replace(
        tzinfo=None
    ) == sample_user_schema.updated_at.replace(tzinfo=None)
    assert user.password_updated_at.replace(
        tzinfo=None
    ) == sample_user_schema.password_updated_at.replace(tzinfo=None)


@pytest.mark.asyncio
async def test_get_user_not_found(
    user_repo: SQLiteUserRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_id = uuid.uuid4()
    mock_cursor.fetchone.return_value = None

    real_repo = SQLiteUserRepository(mock_connection)
    user = await real_repo.get(user_id)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE id = ?", (str(user_id),)
    )
    mock_cursor.fetchone.assert_called_once()
    assert user is None


@pytest.mark.asyncio
async def test_get_by_username_found(
    user_repo: SQLiteUserRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_user_data: tuple,
    sample_user_schema: User,
):
    username = sample_user_schema.username
    mock_cursor.fetchone.return_value = sample_user_data

    real_repo = SQLiteUserRepository(mock_connection)
    user = await real_repo.get_by_username(username)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE username = ?", (username,)
    )
    mock_cursor.fetchone.assert_called_once()
    assert user is not None
    assert user.username == username
    assert user.id == sample_user_schema.id
    assert user.name == sample_user_schema.name
    assert user.hashed_password == sample_user_schema.hashed_password
    assert user.created_at.replace(
        tzinfo=None
    ) == sample_user_schema.created_at.replace(tzinfo=None)
    assert user.updated_at.replace(
        tzinfo=None
    ) == sample_user_schema.updated_at.replace(tzinfo=None)
    assert user.password_updated_at.replace(
        tzinfo=None
    ) == sample_user_schema.password_updated_at.replace(tzinfo=None)


@pytest.mark.asyncio
async def test_get_by_username_not_found(
    user_repo: SQLiteUserRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    username = "nonexistent"
    mock_cursor.fetchone.return_value = None

    real_repo = SQLiteUserRepository(mock_connection)
    user = await real_repo.get_by_username(username)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT * FROM users WHERE username = ?", (username,)
    )
    mock_cursor.fetchone.assert_called_once()
    assert user is None


@pytest.mark.asyncio
async def test_create_user_success(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_user_schema: User,
):
    create_data = CreateUser(
        username="newuser",
        name="New User",
        hashed_password="new_hashed_password",
    )
    repo = SQLiteUserRepository(mock_connection)
    repo.get_by_username = AsyncMock(return_value=sample_user_schema)

    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with (
        patch(
            "mood_diary.backend.repositories.sqlite.user.uuid4",
            return_value=sample_user_schema.id,
        ),
        patch(
            "mood_diary.backend.repositories.sqlite.user.datetime",
            Mock(now=Mock(return_value=fixed_time)),
        ),
    ):
        created_user = await repo.create(create_data)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        ANY,
        (
            str(sample_user_schema.id),
            create_data.username,
            create_data.name,
            create_data.hashed_password,
            fixed_time,
            fixed_time,
            fixed_time,
        ),
    )
    assert "INSERT INTO users" in mock_cursor.execute.call_args[0][0]
    mock_connection.commit.assert_called_once()
    repo.get_by_username.assert_awaited_once_with(create_data.username)
    assert created_user == sample_user_schema


@pytest.mark.asyncio
async def test_create_user_integrity_error(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    create_data = CreateUser(
        username="existinguser",
        name="Existing User",
        hashed_password="existing_password",
    )
    mock_cursor.execute.side_effect = sqlite3.IntegrityError
    repo = SQLiteUserRepository(mock_connection)
    repo.get_by_username = AsyncMock()

    created_user = await repo.create(create_data)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    mock_connection.commit.assert_not_called()
    repo.get_by_username.assert_not_awaited()
    assert created_user is None


@pytest.mark.asyncio
async def test_update_profile_success(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_user_schema: User,
):
    user_id = sample_user_schema.id
    update_data = UpdateUserProfile(name="Updated Name")
    repo = SQLiteUserRepository(mock_connection)
    repo.get = AsyncMock(return_value=sample_user_schema)

    assert isinstance(update_data, UpdateUserProfile)
    updated_user = await repo.update_profile(user_id, update_data)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "UPDATE users SET name = ?, updated_at = ? WHERE id = ?",
        (update_data.name, ANY, str(user_id)),
    )
    mock_connection.commit.assert_called_once()
    repo.get.assert_awaited_once_with(user_id)
    assert updated_user == sample_user_schema


@pytest.mark.asyncio
async def test_update_hashed_password_success(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_user_schema: User,
):
    user_id = sample_user_schema.id
    update_data = UpdateUserHashedPassword(
        hashed_password="new_hashed_password"
    )
    repo = SQLiteUserRepository(mock_connection)
    repo.get = AsyncMock(return_value=sample_user_schema)

    assert isinstance(update_data, UpdateUserHashedPassword)
    updated_user = await repo.update_hashed_password(user_id, update_data)

    mock_connection.cursor.assert_called_once()
    assert mock_cursor.execute.call_count == 1
    call_args = mock_cursor.execute.call_args[0]
    sql_statement = call_args[0]
    sql_params = call_args[1]

    assert "UPDATE users" in sql_statement
    assert "SET hashed_password = ?" in sql_statement
    assert "password_updated_at = ?" in sql_statement
    assert "WHERE id = ?" in sql_statement

    assert sql_params[0] == update_data.hashed_password
    assert isinstance(sql_params[1], datetime)
    assert sql_params[2] == str(user_id)

    mock_connection.commit.assert_called_once()
    repo.get.assert_awaited_once_with(user_id)
    assert updated_user == sample_user_schema
