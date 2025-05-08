import uuid
from datetime import datetime, date, timezone
from unittest.mock import ANY, AsyncMock, MagicMock, patch
from typing import Union

import pytest

from mood_diary.backend.repositories.sqlite.mood import SQLiteMoodRepository
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp,
    MoodStampFilter,
)
from mood_diary.backend.exceptions.mood import (
    MoodStampAlreadyExistsErrorRepo,
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
    mock_connection.cursor.assert_called()
    mock_cursor.execute.assert_called_with(ANY)
    assert (
        "CREATE TABLE IF NOT EXISTS moodstamps"
        in mock_cursor.execute.call_args_list[0][0][0]
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

    repo = SQLiteMoodRepository(mock_connection)
    mood = await repo.get(user_id, mood_date)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert mood is not None
    assert mood.id == sample_mood_schema.id
    assert mood.user_id == sample_mood_schema.user_id
    assert mood.date == sample_mood_schema.date
    assert mood.value == sample_mood_schema.value
    assert mood.note == sample_mood_schema.note
    assert mood.created_at.replace(
        tzinfo=None
    ) == sample_mood_schema.created_at.replace(tzinfo=None)
    assert mood.updated_at.replace(
        tzinfo=None
    ) == sample_mood_schema.updated_at.replace(tzinfo=None)


@pytest.mark.asyncio
async def test_get_moodstamp_not_found(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_id = uuid.uuid4()
    mood_date = date.today()
    mock_cursor.fetchone.return_value = None

    repo = SQLiteMoodRepository(mock_connection)
    mood = await repo.get(user_id, mood_date)

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

    repo = SQLiteMoodRepository(mock_connection)
    moods = await repo.get_many(user_id, filter_body)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert isinstance(moods, list)
    assert len(moods) == 1
    mood = moods[0]
    assert mood.id == uuid.UUID(sample_mood_data[0])
    assert mood.user_id == uuid.UUID(sample_mood_data[1])
    assert mood.date == sample_mood_data[2]
    assert mood.value == sample_mood_data[3]
    assert mood.note == sample_mood_data[4]


@pytest.mark.parametrize(
    "filter_input, expected_sql_clauses, expected_params_indices",
    [
        (MoodStampFilter(start_date=None, end_date=None, value=None), [], [0]),
        (
            MoodStampFilter(
                start_date=date(2024, 1, 1), end_date=None, value=None
            ),
            ["AND date >= ?"],
            [0, 1],
        ),
        (
            MoodStampFilter(
                start_date=None, end_date=date(2024, 12, 31), value=None
            ),
            ["AND date <= ?"],
            [0, 1],
        ),
        (
            MoodStampFilter(start_date=None, end_date=None, value=7),
            ["AND value = ?"],
            [0, 1],
        ),
        (
            MoodStampFilter(
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 31),
                value=5,
            ),
            ["AND date >= ?", "AND date <= ?", "AND value = ?"],
            [0, 1, 2, 3],
        ),
    ],
)
@pytest.mark.asyncio
async def test_get_many_moodstamps_filtered(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_data: tuple,
    filter_input: MoodStampFilter,
    expected_sql_clauses: list[str],
    expected_params_indices: list[int],
):
    user_id = uuid.uuid4()
    mock_cursor.fetchall.return_value = [
        dict(
            id=sample_mood_data[0],
            user_id=str(user_id),
            date=sample_mood_data[2],
            value=sample_mood_data[3],
            note=sample_mood_data[4],
            created_at=sample_mood_data[5],
            updated_at=sample_mood_data[6],
        )
    ]

    repo = SQLiteMoodRepository(mock_connection)
    moods = await repo.get_many(user_id, filter_input)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()

    actual_sql, actual_params = mock_cursor.execute.call_args[0]
    base_query = "SELECT * FROM moodstamps WHERE user_id = ?"
    assert actual_sql.startswith(base_query)
    for clause in expected_sql_clauses:
        assert clause in actual_sql

    expected_params: list[Union[str, date, int]] = [str(user_id)]
    if filter_input.start_date:
        expected_params.append(filter_input.start_date)
    if filter_input.end_date:
        expected_params.append(filter_input.end_date)
    if filter_input.value:
        expected_params.append(filter_input.value)

    assert len(actual_params) == len(expected_params)
    assert list(actual_params) == expected_params

    assert isinstance(moods, list)
    assert len(moods) == 1
    assert moods[0].id == uuid.UUID(sample_mood_data[0])


@pytest.mark.asyncio
async def test_create_moodstamp_success(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_schema: MoodStamp,
):
    """Tests successful creation of a moodstamp."""
    create_data = CreateMoodStamp(
        date=sample_mood_schema.date,
        user_id=sample_mood_schema.user_id,
        value=sample_mood_schema.value,
        note=sample_mood_schema.note,
    )
    repo = SQLiteMoodRepository(mock_connection)
    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    test_uuid = uuid.uuid4()

    expected_moodstamp = sample_mood_schema.model_copy(
        update={
            "id": test_uuid,
            "user_id": sample_mood_schema.user_id,
            "date": create_data.date,
            "value": create_data.value,
            "note": create_data.note,
            "created_at": fixed_time,
            "updated_at": fixed_time,
        }
    )
    repo.get = AsyncMock(return_value=expected_moodstamp)

    with patch(
        "mood_diary.backend.repositories.sqlite.mood.uuid4",
        return_value=test_uuid,
    ) as mock_uuid:
        with patch(
            "mood_diary.backend.repositories.sqlite.mood.datetime"
        ) as mock_dt:
            mock_dt.now.return_value = fixed_time

            created_moodstamp = await repo.create(
                sample_mood_schema.user_id, create_data
            )

    mock_connection.cursor.assert_called_once()
    assert mock_cursor.execute.call_count == 2

    insert_call_args = mock_cursor.execute.call_args_list[1]
    assert "INSERT INTO moodstamps" in insert_call_args[0][0]
    assert insert_call_args[0][1] == (
        str(test_uuid),
        str(sample_mood_schema.user_id),
        create_data.date,
        create_data.value,
        create_data.note,
        fixed_time,
        fixed_time,
    )

    mock_connection.cursor.assert_called()
    assert mock_cursor.execute.call_count >= 1
    assert "INSERT INTO moodstamps" in mock_cursor.execute.call_args[0][0]

    mock_connection.commit.assert_called_once()
    assert created_moodstamp == expected_moodstamp


@pytest.mark.asyncio
async def test_create_moodstamp_duplicate(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    """Tests creating a moodstamp when one already exists for the date."""
    create_data = CreateMoodStamp(
        user_id=uuid.uuid4(),
        date=date.today(),
        value=5,
        note="Already exists",
    )
    mock_cursor.fetchone.return_value = (str(uuid.uuid4()),)

    with pytest.raises(MoodStampAlreadyExistsErrorRepo):
        await mood_repo.create(create_data.user_id, create_data)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with(
        "SELECT id FROM moodstamps WHERE user_id = ? AND date = ?",
        (str(create_data.user_id), create_data.date),
    )
    mock_cursor.fetchone.assert_called_once()
    mock_connection.commit.assert_not_called()


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
    repo = SQLiteMoodRepository(mock_connection)

    original_row_dict = {
        "id": str(sample_mood_schema.id),
        "user_id": str(user_id),
        "date": mood_date,
        "value": sample_mood_schema.value,
        "note": sample_mood_schema.note,
        "created_at": sample_mood_schema.created_at,
        "updated_at": sample_mood_schema.updated_at,
    }
    mock_cursor.fetchone.return_value = original_row_dict

    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with patch(
        "mood_diary.backend.repositories.sqlite.mood.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = fixed_time

        updated_moodstamp = await repo.update(user_id, mood_date, update_data)

    assert updated_moodstamp is not None
    assert updated_moodstamp.value == update_data.value
    assert updated_moodstamp.note == update_data.note
    assert updated_moodstamp.updated_at == fixed_time
    assert updated_moodstamp.id == sample_mood_schema.id
    assert updated_moodstamp.created_at == sample_mood_schema.created_at

    assert mock_cursor.execute.call_count == 2
    select_call = mock_cursor.execute.call_args_list[0]
    assert (
        "SELECT * FROM moodstamps WHERE user_id = ? AND date = ?"
        in select_call[0][0]
    )
    assert select_call[0][1] == (str(user_id), mood_date)
    update_call = mock_cursor.execute.call_args_list[1]
    update_sql = update_call[0][0]
    update_params = update_call[0][1]
    assert "UPDATE moodstamps" in update_sql
    assert "SET value = ?" in update_sql
    assert "note = ?" in update_sql
    assert "updated_at = ?" in update_sql
    assert "WHERE user_id = ? AND date = ?" in update_sql
    assert update_params == (
        update_data.value,
        update_data.note,
        fixed_time,
        str(user_id),
        mood_date,
    )
    mock_connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_moodstamp_only_value(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_schema: MoodStamp,
):
    """Tests updating only the value of a moodstamp."""
    update_data = UpdateMoodStamp(value=9, note=None)
    user_id = sample_mood_schema.user_id
    mood_date = sample_mood_schema.date
    repo = SQLiteMoodRepository(mock_connection)

    original_row_dict = {
        "id": str(sample_mood_schema.id),
        "user_id": str(user_id),
        "date": mood_date,
        "value": sample_mood_schema.value,
        "note": sample_mood_schema.note,
        "created_at": sample_mood_schema.created_at,
        "updated_at": sample_mood_schema.updated_at,
    }
    mock_cursor.fetchone.return_value = original_row_dict

    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with patch(
        "mood_diary.backend.repositories.sqlite.mood.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = fixed_time
        updated_moodstamp = await repo.update(user_id, mood_date, update_data)

    assert updated_moodstamp is not None
    assert updated_moodstamp.value == update_data.value
    assert updated_moodstamp.note == sample_mood_schema.note
    assert updated_moodstamp.updated_at == fixed_time

    assert mock_cursor.execute.call_count == 2
    update_call = mock_cursor.execute.call_args_list[1]
    assert update_call[0][1] == (
        update_data.value,
        sample_mood_schema.note,
        fixed_time,
        str(user_id),
        mood_date,
    )
    mock_connection.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_moodstamp_only_note(
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
    sample_mood_schema: MoodStamp,
):
    """Tests updating only the note of a moodstamp."""
    update_data = UpdateMoodStamp(value=None, note="Only note updated")
    user_id = sample_mood_schema.user_id
    mood_date = sample_mood_schema.date
    repo = SQLiteMoodRepository(mock_connection)

    original_row_dict = {
        "id": str(sample_mood_schema.id),
        "user_id": str(user_id),
        "date": mood_date,
        "value": sample_mood_schema.value,
        "note": sample_mood_schema.note,
        "created_at": sample_mood_schema.created_at,
        "updated_at": sample_mood_schema.updated_at,
    }
    mock_cursor.fetchone.return_value = original_row_dict

    fixed_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    with patch(
        "mood_diary.backend.repositories.sqlite.mood.datetime"
    ) as mock_dt:
        mock_dt.now.return_value = fixed_time
        updated_moodstamp = await repo.update(user_id, mood_date, update_data)

    assert updated_moodstamp is not None
    assert updated_moodstamp.value == sample_mood_schema.value
    assert updated_moodstamp.note == update_data.note
    assert updated_moodstamp.updated_at == fixed_time

    assert mock_cursor.execute.call_count == 2
    update_call = mock_cursor.execute.call_args_list[1]
    assert update_call[0][1] == (
        sample_mood_schema.value,
        update_data.note,
        fixed_time,
        str(user_id),
        mood_date,
    )
    mock_connection.commit.assert_called_once()


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

    repo = SQLiteMoodRepository(mock_connection)
    updated_mood = await repo.update(user_id, mood_date, update_data)

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

    repo = SQLiteMoodRepository(mock_connection)
    deleted_mood = await repo.delete(user_id, mood_date)

    mock_connection.cursor.assert_called()
    assert mock_cursor.execute.call_count >= 2
    mock_connection.commit.assert_called_once()
    assert deleted_mood is not None
    assert deleted_mood.id == sample_mood_schema.id
    assert deleted_mood.user_id == user_id
    assert deleted_mood.date == mood_date
    assert deleted_mood.value == sample_mood_schema.value
    assert deleted_mood.note == sample_mood_schema.note
    assert deleted_mood.created_at.replace(
        tzinfo=None
    ) == sample_mood_schema.created_at.replace(tzinfo=None)
    assert deleted_mood.updated_at.replace(
        tzinfo=None
    ) == sample_mood_schema.updated_at.replace(tzinfo=None)


@pytest.mark.asyncio
async def test_delete_moodstamp_not_found(
    mood_repo: SQLiteMoodRepository,
    mock_connection: AsyncMock,
    mock_cursor: MagicMock,
):
    user_id = uuid.uuid4()
    mood_date = date.today()

    mock_cursor.fetchone.return_value = None

    repo = SQLiteMoodRepository(mock_connection)
    deleted_mood = await repo.delete(user_id, mood_date)

    mock_connection.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    assert deleted_mood is None
