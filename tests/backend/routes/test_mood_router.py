import uuid
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI, status
from fastapi.testclient import TestClient

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

# Import app factory and settings
from mood_diary.backend.app import get_app
from mood_diary.backend.config import Settings

from mood_diary.backend.routes.mood import router as mood_router


# --- Fixtures ---

@pytest.fixture
def mock_mood_service() -> AsyncMock:
    return AsyncMock(spec=MoodService)


@pytest.fixture
def test_user_id() -> uuid.UUID:
    return uuid.uuid4()


# Fixture for the main application instance
@pytest.fixture
def main_app() -> FastAPI:
    # Use a specific secret key for tests if needed, or default settings
    return get_app(Settings(AUTH_TOKEN_SECRET_KEY="test-mood-secret-key"))


# Fixture to override dependencies specifically for mood tests
@pytest.fixture
def override_mood_dependencies(
    main_app: FastAPI, # Depend on the real app
    test_user_id: uuid.UUID,
    mock_mood_service: AsyncMock
):
    async def override_get_current_user_id() -> uuid.UUID:
        return test_user_id

    def override_get_mood_service() -> MoodService:
        return mock_mood_service

    main_app.dependency_overrides[get_current_user_id] = override_get_current_user_id
    main_app.dependency_overrides[get_mood_service] = override_get_mood_service

    yield # Allow tests to run with overrides

    # Clean up overrides after tests
    main_app.dependency_overrides = {}


# Updated client fixture
@pytest.fixture
def client_mood(main_app: FastAPI, override_mood_dependencies) -> TestClient:
    # Client now uses the main_app with overrides applied
    with TestClient(main_app) as client:
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
    response = client_mood.post("/api/mood/", json=create_payload)

    assert response.status_code == status.HTTP_200_OK
    response_data = response.json()
    assert response_data == sample_mood_stamp_schema.model_dump(mode='json')

    mock_mood_service.create.assert_awaited_once()
    call_args = mock_mood_service.create.call_args[1]
    assert call_args['user_id'] == test_user_id
    assert isinstance(call_args['body'], CreateMoodStampRequest)
    assert call_args['body'].value == create_payload["value"]
    assert call_args['body'].note == create_payload["note"]


@pytest.mark.parametrize(
    "payload_update, expected_status",
    [
        # Valid boundary values
        ({"value": 1, "note": "Min value"}, status.HTTP_200_OK),
        ({"value": 10, "note": "Max value"}, status.HTTP_200_OK),
        # Invalid values (outside 1-10)
        ({"value": 0, "note": "Too low"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        ({"value": 11, "note": "Too high"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        # Invalid type
        ({"value": "not-an-int", "note": "Wrong type"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        # Missing value
        ({"note": "Missing value"}, status.HTTP_422_UNPROCESSABLE_ENTITY),
        # Missing note (should be ok, assuming default or handling)
        # Note: The schema requires 'note', so this should fail validation if note is truly missing.
        # Let's test missing 'note' explicitly if the schema requires it.
        ({"value": 5}, status.HTTP_422_UNPROCESSABLE_ENTITY), # Test missing note
    ]
)
def test_create_moodstamp_validation_error(
        client_mood: TestClient,
        mock_mood_service: AsyncMock, # Add mock service to handle valid cases
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema, # Needed for valid cases
        payload_update: dict,
        expected_status: int,
):
    """Tests validation errors and boundary values for creating moodstamps."""
    today_str = date.today().isoformat()
    base_payload = {"date": today_str, "user_id": str(test_user_id)}

    # Update base payload with current test case specifics
    payload = base_payload.copy()
    payload.update(payload_update)

    # If the expected status is OK, set up the mock service
    if expected_status == status.HTTP_200_OK:
        # Use sample schema but update value/note from payload if they exist
        schema_dict = sample_mood_stamp_schema.model_dump()
        if "value" in payload: schema_dict["value"] = payload["value"]
        if "note" in payload: schema_dict["note"] = payload["note"]
        schema_dict["date"] = date.fromisoformat(today_str)
        mock_mood_service.create.return_value = MoodStampSchema(**schema_dict)
        mock_mood_service.create.side_effect = None # Ensure no side effect is active
    elif expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        # Ensure the service is not called for validation errors
        mock_mood_service.create.reset_mock()
        mock_mood_service.create.side_effect = None # Just in case

    response = client_mood.post("/api/mood/", json=payload)

    assert response.status_code == expected_status

    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        # Check that the service method was NOT called
        mock_mood_service.create.assert_not_awaited()
        # Optional: Check details in the response body for 422 errors
        assert "detail" in response.json()
    elif expected_status == status.HTTP_200_OK:
        # Check that the service method WAS called for valid cases
        mock_mood_service.create.assert_awaited_once()


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
    # Test that the specific exception from the service translates to the correct HTTP response
    response = client_mood.post("/api/mood/", json=create_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "MoodStamp already exists"}
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

    response = client_mood.get(f"/api/mood/{test_date_str}")

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

    # Test that the specific exception from the service translates to the correct HTTP response
    response = client_mood.get(f"/api/mood/{test_date_str}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "MoodStamp does not exist"}
    mock_mood_service.get.assert_awaited_once_with(user_id=test_user_id, date=test_date)


def test_get_many_moodstamps_success_no_filters(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    mock_mood_service.get_many.return_value = [sample_mood_stamp_schema]

    response = client_mood.get("/api/mood/")

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

    response = client_mood.get(
        f"/api/mood/?start_date={start_date_str}&end_date={end_date_str}&value={value_filter}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [sample_mood_stamp_schema.model_dump(mode='json')]
    mock_mood_service.get_many.assert_awaited_once()
    call_args = mock_mood_service.get_many.call_args[1]
    assert call_args['user_id'] == test_user_id
    assert isinstance(call_args['body'], GetManyMoodStampsRequest)
    assert call_args['body'].start_date == date.fromisoformat(start_date_str)
    assert call_args['body'].end_date == date.fromisoformat(end_date_str)
    assert call_args['body'].value == value_filter


@pytest.mark.parametrize(
    "query_params, expected_status, expected_loc",
    [
        # Invalid start_date format
        ({"start_date": "not-a-date"}, status.HTTP_422_UNPROCESSABLE_ENTITY, ["query", "start_date"]),
        # Invalid end_date format
        ({"end_date": "invalid-date"}, status.HTTP_422_UNPROCESSABLE_ENTITY, ["query", "end_date"]),
        # Invalid value format
        ({"value": "not-an-int"}, status.HTTP_422_UNPROCESSABLE_ENTITY, ["query", "value"]),
    ]
)
def test_get_many_moodstamps_validation_error(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        query_params: dict,
        expected_status: int,
        expected_loc: list[str],
):
    """Tests validation errors for query parameters in get_many_moodstamps."""
    response = client_mood.get("/api/mood/", params=query_params)

    assert response.status_code == expected_status
    if expected_status == status.HTTP_422_UNPROCESSABLE_ENTITY:
        details = response.json().get("detail", [])
        assert isinstance(details, list)
        assert len(details) > 0
        found_error = False
        for detail in details:
            # Check if the error location matches the expected parameter
            if detail.get("loc") == expected_loc:
                found_error = True
                break
        assert found_error, f"Expected error detail for loc '{expected_loc}' not found in {details}"
        # Ensure service not called
        mock_mood_service.get_many.assert_not_awaited()


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

    response = client_mood.put(f"/api/mood/{test_date_str}", json=update_payload)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == updated_schema.model_dump(mode='json')

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

    # Test that the specific exception from the service translates to the correct HTTP response
    response = client_mood.put(f"/api/mood/{test_date_str}", json=update_payload)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "MoodStamp does not exist"}
    mock_mood_service.update.assert_awaited_once()


@pytest.mark.parametrize(
    "payload, expected_detail_contains",
    [
        # Invalid value type
        ({"value": "not-an-integer", "note": "Invalid type"}, "int_parsing"),
        # Invalid value range
        ({"value": 0, "note": "Too low"}, "greater_than_equal"),
        ({"value": 11, "note": "Too high"}, "less_than_equal"),
        # Invalid note type (if schema changes to validate note length/type)
        # ({"value": 5, "note": 123}, "string_type"), # Example if note validation added
        # Missing both fields (should be invalid, but depends on FastAPI/Pydantic handling)
        #({}, "value_error"), # Expect some validation error if body is empty - Removed as empty body is valid for this schema
    ]
)
def test_update_moodstamp_validation_error(
        client_mood: TestClient,
        payload: dict,
        expected_detail_contains: str,
):
    """Tests validation errors for updating moodstamps."""
    test_date = date.today()
    test_date_str = test_date.isoformat()

    response = client_mood.put(f"/api/mood/{test_date_str}", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    details = response.json().get("detail", [])
    assert isinstance(details, list)
    assert len(details) > 0
    # Check if expected error type/message substring is present in any detail item
    found_error = False
    for detail in details:
        # Check in 'type' field or 'msg' field for the expected error string
        if expected_detail_contains in detail.get("type", "") or \
           expected_detail_contains in detail.get("msg", ""):
            found_error = True
            break
    assert found_error, f"Expected error detail containing '{expected_detail_contains}' not found in {details}"


def test_delete_moodstamp_success(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
        sample_mood_stamp_schema: MoodStampSchema,
):
    test_date = sample_mood_stamp_schema.date
    test_date_str = test_date.isoformat()
    mock_mood_service.delete.return_value = None

    response = client_mood.delete(f"/api/mood/{test_date_str}")

    assert response.status_code == status.HTTP_200_OK
    # Check that the response body is JSON null for successful delete
    assert response.json() is None
    mock_mood_service.delete.assert_awaited_once_with(user_id=test_user_id, date=test_date)


def test_delete_moodstamp_not_found(
        client_mood: TestClient,
        mock_mood_service: AsyncMock,
        test_user_id: uuid.UUID,
):
    test_date = date.today()
    test_date_str = test_date.isoformat()
    mock_mood_service.delete.side_effect = MoodStampNotExist

    # Test that the specific exception from the service translates to the correct HTTP response
    response = client_mood.delete(f"/api/mood/{test_date_str}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "MoodStamp does not exist"}
    mock_mood_service.delete.assert_awaited_once_with(user_id=test_user_id, date=test_date)
