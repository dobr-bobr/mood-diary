import uuid
from datetime import datetime
from sqlite3 import Date
from unittest.mock import AsyncMock

import pytest

from mood_diary.backend.exceptions.mood import (
    MoodStampNotExist,
    MoodStampAlreadyExists,
    MoodStampAlreadyExistsErrorRepo,
)
from mood_diary.backend.repositories.sсhemas.mood import (
    MoodStamp,
    CreateMoodStamp,
    UpdateMoodStamp,
    MoodStampFilter,
)
from mood_diary.backend.services.mood import MoodService
from mood_diary.common.api.schemas.mood import (
    CreateMoodStampRequest,
    UpdateMoodStampRequest,
    GetManyMoodStampsRequest,
)


# --- Fixtures ---


@pytest.fixture
def mock_moodstamp_repository():
    return AsyncMock()


@pytest.fixture
def mood_service(mock_moodstamp_repository):
    return MoodService(moodstamp_repository=mock_moodstamp_repository)


@pytest.fixture
def sample_moodstamp():
    return MoodStamp(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        date=datetime.now().date(),
        value=5,
        note="Feeling good!",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def create_moodstamp_request():
    return CreateMoodStampRequest(
        date=datetime.now().date(),
        value=5,
        note="Feeling good!",
    )


@pytest.fixture
def update_moodstamp_request():
    return UpdateMoodStampRequest(
        value=7,
        note="Updated mood",
    )


# --- Test Cases ---


@pytest.mark.asyncio
async def test_create_moodstamp_success(
    mood_service,
    mock_moodstamp_repository,
    sample_moodstamp,
    create_moodstamp_request,
):
    mock_moodstamp_repository.create.return_value = sample_moodstamp

    result = await mood_service.create(
        sample_moodstamp.user_id, create_moodstamp_request
    )

    mock_moodstamp_repository.create.assert_awaited_once_with(
        user_id=sample_moodstamp.user_id,
        body=CreateMoodStamp(
            user_id=sample_moodstamp.user_id,
            date=create_moodstamp_request.date,
            value=create_moodstamp_request.value,
            note=create_moodstamp_request.note,
        ),
    )

    assert result.id == sample_moodstamp.id
    assert result.value == sample_moodstamp.value
    assert result.note == sample_moodstamp.note


@pytest.mark.asyncio
async def test_create_moodstamp_already_exists(
    mood_service, mock_moodstamp_repository, create_moodstamp_request
):
    mock_moodstamp_repository.create.side_effect = (
        MoodStampAlreadyExistsErrorRepo()
    )

    with pytest.raises(MoodStampAlreadyExists):
        await mood_service.create(uuid.uuid4(), create_moodstamp_request)


@pytest.mark.asyncio
async def test_get_moodstamp_success(
    mood_service, mock_moodstamp_repository, sample_moodstamp
):
    mock_moodstamp_repository.get.return_value = sample_moodstamp
    result = await mood_service.get(
        sample_moodstamp.user_id, sample_moodstamp.date
    )

    mock_moodstamp_repository.get.assert_awaited_once_with(
        user_id=sample_moodstamp.user_id, date=sample_moodstamp.date
    )
    assert result.id == sample_moodstamp.id
    assert result.value == sample_moodstamp.value
    assert result.note == sample_moodstamp.note


@pytest.mark.asyncio
async def test_get_moodstamp_not_found(
    mood_service, mock_moodstamp_repository, sample_moodstamp
):
    mock_moodstamp_repository.get.return_value = None

    with pytest.raises(MoodStampNotExist):
        await mood_service.get(sample_moodstamp.user_id, sample_moodstamp.date)


@pytest.mark.asyncio
async def test_update_moodstamp_success(
    mood_service,
    mock_moodstamp_repository,
    sample_moodstamp,
    update_moodstamp_request,
):
    updated_moodstamp = sample_moodstamp.model_copy(
        update={
            "value": update_moodstamp_request.value,
            "note": update_moodstamp_request.note,
        }
    )

    mock_moodstamp_repository.update.return_value = updated_moodstamp

    result = await mood_service.update(
        sample_moodstamp.user_id,
        sample_moodstamp.date,
        update_moodstamp_request,
    )

    mock_moodstamp_repository.update.assert_awaited_once_with(
        user_id=sample_moodstamp.user_id,
        date=sample_moodstamp.date,
        body=UpdateMoodStamp(
            value=update_moodstamp_request.value,
            note=update_moodstamp_request.note,
        ),
    )

    assert result.id == updated_moodstamp.id
    assert (
        result.value == update_moodstamp_request.value
    )  # Expect value to be updated
    assert result.note == update_moodstamp_request.note


@pytest.mark.asyncio
async def test_update_moodstamp_not_found(
    mood_service, mock_moodstamp_repository, update_moodstamp_request
):
    mock_moodstamp_repository.update.return_value = None

    with pytest.raises(MoodStampNotExist):
        await mood_service.update(
            uuid.uuid4(), datetime.now().date(), update_moodstamp_request
        )


@pytest.mark.asyncio
async def test_get_many_moodstamps_success(
    mood_service, mock_moodstamp_repository, sample_moodstamp
):
    mock_moodstamp_repository.get_many.return_value = [sample_moodstamp]

    result = await mood_service.get_many(
        sample_moodstamp.user_id,
        GetManyMoodStampsRequest(
            start_date=Date(2025, 1, 1),
            end_date=Date(2025, 1, 31),
        ),
    )

    mock_moodstamp_repository.get_many.assert_awaited_once_with(
        user_id=sample_moodstamp.user_id,
        body=MoodStampFilter(
            start_date=Date(2025, 1, 1), end_date=Date(2025, 1, 31), value=None
        ),
    )
    assert len(result) == 1
    assert result[0].id == sample_moodstamp.id


@pytest.mark.asyncio
async def test_delete_moodstamp_success(
    mood_service, mock_moodstamp_repository, sample_moodstamp
):
    mock_moodstamp_repository.delete.return_value = True
    await mood_service.delete(sample_moodstamp.user_id, sample_moodstamp.date)

    mock_moodstamp_repository.delete.assert_awaited_once_with(
        user_id=sample_moodstamp.user_id, date=sample_moodstamp.date
    )


@pytest.mark.asyncio
async def test_delete_moodstamp_not_found(
    mood_service, mock_moodstamp_repository, sample_moodstamp
):
    mock_moodstamp_repository.delete.return_value = False

    with pytest.raises(MoodStampNotExist):
        await mood_service.delete(
            sample_moodstamp.user_id, sample_moodstamp.date
        )
