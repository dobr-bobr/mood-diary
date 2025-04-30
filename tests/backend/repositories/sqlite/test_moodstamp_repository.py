import uuid
from datetime import datetime, date
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest

from mood_diary.backend.repositories.sqlite.mood import SQLiteMoodRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp,
    MoodStampFilter,
)
from tests.backend.repositories.sqlite.base_fixtures import (
    mock_connection,
    mock_cursor,
)


# --- Fixtures ---


@pytest.fixture
def mood_repo(mock_connection):
    repo = SQLiteMoodRepository(mock_connection)
    repo.get = AsyncMock(spec=repo.get)
    repo.get_many = AsyncMock(spec=repo.get_many)
    return repo


@pytest.fixture
def sample_mood_data():
    mood_id = uuid.uuid4()
    now = datetime.now()
    return (
        str(mood_id),
        str(uuid.uuid4()),
        date.today(),
        5,
        "Feeling good!",
        now,
        now,
    )


@pytest.fixture
def sample_mood_schema(sample_mood_data):
    return MoodStamp(
        id=uuid.UUID(sample_mood_data[0]),
        user_id=uuid.UUID(sample_mood_data[1]),
        date=sample_mood_data[2],
        value=sample_mood_data[3],
        note=sample_mood_data[4],
        created_at=sample_mood_data[5],
        updated_at=sample_mood_data[6],
    )


# --- Test Cases ---


def test_init_db(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    mood_repo.init_db()
    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(ANY)
    assert (
        "CREATE TABLE IF NOT EXISTS moodstamps"
        in mock_cursor.execute.call_args[0][0]
    )
    mock_connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_moodstamp_found(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_data: tuple,
    sample_mood_schema: MoodStamp,
):
    user_id = sample_mood_schema.user_id
    mood_date = sample_mood_schema.date
    mock_cursor.fetchone.return_value = dict(
        id=sample_mood_data[0],
        user_id=sample_mood_data[1],
        date=sample_mood_data[2],
        value=sample_mood_data[3],
        note=sample_mood_data[4],
        created_at=sample_mood_data[5],
        updated_at=sample_mood_data[6],
    )

    real_repo = SQLiteMoodRepository(mock_connection)
    mood = await real_repo.get(user_id, mood_date)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert mood is not None
    assert mood.id == sample_mood_schema.id
    assert mood.value == sample_mood_schema.value


@pytest.mark.asyncio
async def test_get_moodstamp_not_found(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_id = uuid.uuid4()
    mood_date = date.today()
    mock_cursor.fetchone.return_value = None

    real_repo = SQLiteMoodRepository(mock_connection)
    mood = await real_repo.get(user_id, mood_date)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert mood is None


@pytest.mark.asyncio
async def test_get_many_moodstamps(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_data: tuple,
):
    user_id = uuid.uuid4()
    filter_body = MoodStampFilter(start_date=None, end_date=None, value=None)
    mock_cursor.fetchall.return_value = [
        dict(
            id=sample_mood_data[0],
            user_id=sample_mood_data[1],
            date=sample_mood_data[2],
            value=sample_mood_data[3],
            note=sample_mood_data[4],
            created_at=sample_mood_data[5],
            updated_at=sample_mood_data[6],
        )
    ]

    real_repo = SQLiteMoodRepository(mock_connection)
    moods = await real_repo.get_many(user_id, filter_body)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert isinstance(moods, list)
    assert len(moods) == 1
    assert moods[0].value == sample_mood_data[3]


@pytest.mark.asyncio
async def test_create_moodstamp_success(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_schema: MoodStamp,
):
    create_data = CreateMoodStamp(
        user_id=sample_mood_schema.user_id,
        date=sample_mood_schema.date,
        value=sample_mood_schema.value,
        note=sample_mood_schema.note,
    )
    mock_cursor.fetchone.return_value = None

    with patch(
        "mood_diary.backend.repositories.sqlite.mood.uuid4",
        return_value=sample_mood_schema.id,
    ):
        created_mood = await mood_repo.create(
            sample_mood_schema.user_id, create_data
        )

    mock_connection.cursor.assert_called()
    assert mock_cursor.execute.call_count >= 2
    assert "INSERT INTO moodStamps" in mock_cursor.execute.call_args[0][0]
    mock_connection.commit.assert_called_once()
    assert created_mood.date == create_data.date


@pytest.mark.asyncio
async def test_create_moodstamp_duplicate(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    create_data = CreateMoodStamp(
        user_id=uuid.uuid4(),
        date=date.today(),
        value=5,
        note="Already exists",
    )
    mock_cursor.fetchone.return_value = (str(uuid.uuid4()),)

    from mood_diary.backend.exceptions.mood import (
        MoodStampAlreadyExistsErrorRepo,
    )

    with pytest.raises(MoodStampAlreadyExistsErrorRepo):
        await mood_repo.create(create_data.user_id, create_data)


@pytest.mark.asyncio
async def test_update_moodstamp_success(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_schema: MoodStamp,
):
    update_data = UpdateMoodStamp(value=7, note="Updated note")
    user_id = sample_mood_schema.user_id
    mood_date = sample_mood_schema.date

    mock_cursor.fetchone.return_value = dict(
        id=str(sample_mood_schema.id),
        user_id=str(user_id),
        date=mood_date,
        value=sample_mood_schema.value,
        note=sample_mood_schema.note,
        created_at=sample_mood_schema.created_at,
        updated_at=sample_mood_schema.updated_at,
    )

    real_repo = SQLiteMoodRepository(mock_connection)
    updated_mood = await real_repo.update(user_id, mood_date, update_data)

    mock_connection.cursor.assert_called()
    mock_cursor.execute.assert_called()
    mock_connection.commit.assert_called_once()
    assert updated_mood.value == update_data.value
    assert updated_mood.note == update_data.note


@pytest.mark.asyncio
async def test_update_moodstamp_not_found(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_id = uuid.uuid4()
    mood_date = date.today()
    update_data = UpdateMoodStamp(value=8)

    mock_cursor.fetchone.return_value = None

    real_repo = SQLiteMoodRepository(mock_connection)
    updated_mood = await real_repo.update(user_id, mood_date, update_data)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert updated_mood is None


@pytest.mark.asyncio
async def test_delete_moodstamp_success(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_schema: MoodStamp,
):
    user_id = sample_mood_schema.user_id
    mood_date = sample_mood_schema.date

    mock_cursor.fetchone.return_value = dict(
        id=str(sample_mood_schema.id),
        user_id=str(user_id),
        date=mood_date,
        value=sample_mood_schema.value,
        note=sample_mood_schema.note,
        created_at=sample_mood_schema.created_at,
        updated_at=sample_mood_schema.updated_at,
    )

    real_repo = SQLiteMoodRepository(mock_connection)
    deleted_mood = await real_repo.delete(user_id, mood_date)

    mock_connection.cursor.assert_called()
    assert mock_cursor.execute.call_count >= 2
    mock_connection.commit.assert_called_once()
    assert deleted_mood.value == sample_mood_schema.value


@pytest.mark.asyncio
async def test_delete_moodstamp_not_found(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_id = uuid.uuid4()
    mood_date = date.today()

    mock_cursor.fetchone.return_value = None

    real_repo = SQLiteMoodRepository(mock_connection)
    deleted_mood = await real_repo.delete(user_id, mood_date)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert deleted_mood is None
