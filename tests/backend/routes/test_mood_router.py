import uuid
from datetime import date, datetime, timezone
from typing import Generator
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, status, Cookie
from fastapi.testclient import TestClient

from mood_diary.backend.exceptions.user import InvalidOrExpiredAccessToken
from mood_diary.backend.exceptions.mood import MoodStampAlreadyExists, MoodStampNotExist
from mood_diary.backend.routes.dependencies import (
    get_mood_service,
    get_current_user_id,
)
from mood_diary.backend.services.mood import MoodService
from mood_diary.common.api.schemas.mood import (
    CreateMoodStampRequest,
    GetManyMoodStampsRequest,
    UpdateMoodStampRequest,
    MoodStampSchema,
)

from mood_diary.backend.routes.mood import router as mood_router


# --- Fixtures ---

@pytest.fixture
def mock_mood_service() -> AsyncMock:
    return AsyncMock(spec=MoodService)


@pytest.fixture
def test_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def main_app_mood(test_user_id: uuid.UUID, mock_mood_service: AsyncMock) -> FastAPI:
    app = FastAPI()
    app.include_router(mood_router, prefix="/api/moods", tags=["moods"])

    async def override_get_current_user_id(access_token: str | None = Cookie(None)) -> uuid.UUID:
        if not access_token:
            raise InvalidOrExpiredAccessToken()
        return test_user_id

    def override_get_mood_service() -> MoodService:
        return mock_mood_service

    app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    app.dependency_overrides[get_mood_service] = override_get_mood_service

    return app


@pytest.fixture
def client_mood(main_app_mood: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(main_app_mood) as client:
        yield client


@pytest.fixture
def sample_mood_stamp_data(test_user_id: uuid.UUID) -> dict:
    today = date.today()
    now = datetime.now(timezone.utc)
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(test_user_id),
        "date": today.isoformat(),
        "value": 5,
        "note": "Feeling good today!",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "updated_at": now.isoformat().replace("+00:00", "Z"),
    }


@pytest.fixture
def sample_mood_stamp_schema(sample_mood_stamp_data: dict) -> MoodStampSchema:
    data = sample_mood_stamp_data.copy()
    data["date"] = date.fromisoformat(data["date"])
    data["created_at"] = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
    data["updated_at"] = datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
    return MoodStampSchema(**data)


# --- Test Cases ---

def test_create_moodstamp_success(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    mock_mood_service.create.return_value = sample_mood_stamp_schema
    today_str = sample_mood_stamp_schema.date.isoformat()

    create_payload = {"date": today_str,
                      "user_id": str(test_user_id),
                      "value": 5,
                      "note": "Feeling good today!"
                      }
    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.post("/api/moods/", json=create_payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data["user_id"] == str(test_user_id)
    assert response_data["value"] == create_payload["value"]
    assert response_data["note"] == create_payload["note"]

    mock_mood_service.create.assert_awaited_once()
    call_args = mock_mood_service.create.call_args[1]
    assert call_args['user_id'] == test_user_id
    assert isinstance(call_args['body'], CreateMoodStampRequest)
    assert call_args['body'].value == create_payload["value"]
    assert call_args['body'].note == create_payload["note"]


def test_create_moodstamp_already_exists(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
):
    mock_mood_service.create.side_effect = MoodStampAlreadyExists()

    create_payload = {
        "date": date.today().isoformat(),
        "user_id": str(test_user_id),
        "value": 3,
        "note": "Already here"
    }
    client_mood.cookies.set("access_token", "fake-test-token")
    with pytest.raises(MoodStampAlreadyExists):
        client_mood.post("/api/moods/", json=create_payload)
    mock_mood_service.create.assert_awaited_once()


def test_get_moodstamp_success(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    test_date = sample_mood_stamp_schema.date
    test_date_str = test_date.isoformat()
    mock_mood_service.get.return_value = sample_mood_stamp_schema

    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.get(f"/api/moods/{test_date_str}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == sample_mood_stamp_schema.model_dump(mode='json')
    mock_mood_service.get.assert_awaited_once_with(user_id=test_user_id, date=test_date)


def test_get_moodstamp_not_found(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
):
    test_date = date.today()
    test_date_str = test_date.isoformat()
    mock_mood_service.get.side_effect = MoodStampNotExist()

    client_mood.cookies.set("access_token", "fake-test-token")
    with pytest.raises(MoodStampNotExist):
        client_mood.get(f"/api/moods/{test_date_str}")
    mock_mood_service.get.assert_awaited_once_with(user_id=test_user_id, date=test_date)


def test_get_many_moodstamps_success_no_filters(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    mock_mood_service.get_many.return_value = [sample_mood_stamp_schema]

    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.get("/api/moods/")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [sample_mood_stamp_schema.model_dump(mode='json')]
    mock_mood_service.get_many.assert_awaited_once()
    call_args = mock_mood_service.get_many.call_args[1]
    assert call_args['user_id'] == test_user_id
    assert isinstance(call_args['body'], GetManyMoodStampsRequest)
    assert call_args['body'].start_date is None
    assert call_args['body'].end_date is None
    assert call_args['body'].value is None


def test_get_many_moodstamps_success_with_filters(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    mock_mood_service.get_many.return_value = [sample_mood_stamp_schema]
    start_date_str = "2023-01-01"
    end_date_str = "2023-12-31"
    value_filter = 5

    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.get(
        f"/api/moods/?start_date={start_date_str}&end_date={end_date_str}&value={value_filter}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [sample_mood_stamp_schema.model_dump(mode='json')]
    mock_mood_service.get_many.assert_awaited_once()
    call_args = mock_mood_service.get_many.call_args[1]
    assert call_args['user_id'] == test_user_id
    assert isinstance(call_args['body'], GetManyMoodStampsRequest)
    assert call_args['body'].start_date == date.fromisoformat(start_date_str)
    assert call_args['body'].end_date == date.fromisoformat(end_date_str)
    assert call_args['body'].value == value_filter


def test_update_moodstamp_success(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    test_date = sample_mood_stamp_schema.date
    test_date_str = test_date.isoformat()
    update_payload = {
        "value": 4,
        "note": "Updated note"
    }
    updated_schema = sample_mood_stamp_schema.model_copy(update=update_payload)
    mock_mood_service.update.return_value = updated_schema

    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.put(f"/api/moods/{test_date_str}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    mock_mood_service.update.assert_awaited_once()
    call_args = mock_mood_service.update.call_args[1]
    assert call_args['user_id'] == test_user_id
    assert call_args['date'] == test_date
    assert isinstance(call_args['body'], UpdateMoodStampRequest)
    assert call_args['body'].value == update_payload["value"]
    assert call_args['body'].note == update_payload["note"]


def test_update_moodstamp_not_found(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
):
    test_date = date.today()
    test_date_str = test_date.isoformat()
    update_payload = {"value": 4, "note": "Trying to update non-existent"}
    mock_mood_service.update.side_effect = MoodStampNotExist

    client_mood.cookies.set("access_token", "fake-test-token")
    with pytest.raises(MoodStampNotExist):
        client_mood.put(f"/api/moods/{test_date_str}", json=update_payload)
    mock_mood_service.update.assert_awaited_once()


def test_update_moodstamp_validation_error(
        client_mood: TestClient,
):
    test_date = date.today()
    test_date_str = test_date.isoformat()
    invalid_payload = {"value": "not-an-integer", "note": "Invalid data"}

    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.put(f"/api/moods/{test_date_str}", json=invalid_payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "detail" in response.json()
    assert response.json()["detail"][0]["type"] == "int_parsing"  # Пример


def test_delete_moodstamp_success(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    test_date = sample_mood_stamp_schema.date
    test_date_str = test_date.isoformat()
    mock_mood_service.delete.return_value = None

    client_mood.cookies.set("access_token", "fake-test-token")
    response = client_mood.delete(f"/api/moods/{test_date_str}")

    assert response.status_code == status.HTTP_200_OK
    mock_mood_service.delete.assert_awaited_once_with(user_id=test_user_id, date=test_date)


def test_delete_moodstamp_not_found(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
):
    test_date = date.today()
    test_date_str = test_date.isoformat()
    mock_mood_service.delete.side_effect = MoodStampNotExist

    client_mood.cookies.set("access_token", "fake-test-token")
    with pytest.raises(MoodStampNotExist):
        client_mood.delete(f"/api/moods/{test_date_str}")
    mock_mood_service.delete.assert_awaited_once_with(user_id=test_user_id, date=test_date)
