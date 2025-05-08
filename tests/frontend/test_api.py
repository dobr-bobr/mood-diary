import pytest
from unittest.mock import MagicMock, patch
from datetime import date

from mood_diary.frontend.shared.api import api


@pytest.fixture
def mock_session():
    session = MagicMock()
    with patch("mood_diary.frontend.shared.api.api.provide_requests_session", return_value=session):
        yield session


@pytest.fixture(autouse=True)
def mock_streamlit():
    with patch("mood_diary.frontend.shared.api.api.st") as mock_st:
        yield mock_st


def test_fetch_profile_success(mock_session, mock_streamlit):
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.json.return_value = {"name": "John"}

    api.fetch_profile()
    assert mock_streamlit.session_state.name == "John"


def test_fetch_profile_unauthorized(mock_session, mock_streamlit):
    mock_session.get.return_value.status_code = 401
    api.fetch_profile()
    mock_streamlit.switch_page.assert_called_once()


def test_fetch_change_name_success(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 200
    mock_session.put.return_value.json.return_value = {"name": "NewName"}

    api.fetch_change_name("NewName")
    assert mock_streamlit.session_state.name == "NewName"


def test_fetch_change_password_success(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 200

    api.fetch_change_password("oldpass", "newpass")
    mock_streamlit.info.assert_called_once_with("Password successfully changed")
    mock_streamlit.switch_page.assert_called_once_with("main.py")


def test_fetch_all_mood_success(mock_session, mock_streamlit):
    mock_session.get.return_value.status_code = 200
    mock_session.get.return_value.json.return_value = [{"date": "2024-01-01", "value": 3}]

    result = api.fetch_all_mood()
    assert result == [{"date": "2024-01-01", "value": 3}]


def test_fetch_create_mood_success(mock_session, mock_streamlit):
    mock_session.post.return_value.status_code = 200

    result = api.fetch_create_mood(date.today(), 3, "note")
    assert result is True
    mock_streamlit.success.assert_called_once()


def test_fetch_create_mood_duplicate(mock_session, mock_streamlit):
    mock_session.post.return_value.status_code = 400
    mock_session.post.return_value.json.return_value = {"detail": "Already exists"}

    result = api.fetch_create_mood(date.today(), 3, "note")
    assert result is False
    mock_streamlit.warning.assert_called_once_with("Already exists")


def test_fetch_delete_mood_success(mock_session, mock_streamlit):
    mock_session.delete.return_value.status_code = 200
    mock_session.delete.return_value.json.return_value = {"status": "deleted"}

    result = api.fetch_delete_mood("2024-01-01")
    assert result == {"status": "deleted"}


def test_fetch_edit_mood_success(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 200
    mock_session.put.return_value.json.return_value = {"date": "2024-01-01", "value": 2}

    result = api.fetch_edit_mood("2024-01-01", value=2)
    assert result["value"] == 2


def test_fetch_profile_server_error(mock_session, mock_streamlit):
    mock_session.get.return_value.status_code = 500
    api.fetch_profile()
    mock_streamlit.error.assert_called_once_with("Failed to load user profile")
    mock_streamlit.stop.assert_called_once()


def test_fetch_profile_exception(mock_session, mock_streamlit):
    mock_session.get.side_effect = Exception("Network error")
    api.fetch_profile()
    mock_streamlit.error.assert_called_once()
    assert "Error fetching profile" in mock_streamlit.error.call_args[0][0]


def test_fetch_change_name_unauthorized(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 401
    api.fetch_change_name("AnotherName")
    mock_streamlit.switch_page.assert_called_once_with("pages/authorization.py")


def test_fetch_change_name_server_error(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 500
    api.fetch_change_name("BadName")
    mock_streamlit.error.assert_called_once_with("Failed to change name")
    mock_streamlit.stop.assert_called_once()


def test_fetch_change_password_unauthorized(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 401
    api.fetch_change_password("wrong", "new")
    mock_streamlit.switch_page.assert_called_once_with("pages/authorization.py")


def test_fetch_change_password_server_error(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 500
    mock_session.put.return_value.text = "Internal Server Error"
    api.fetch_change_password("old", "new")
    mock_streamlit.error.assert_called_once()
    assert "Failed to change password" in mock_streamlit.error.call_args[0][0]


def test_fetch_all_mood_unauthorized(mock_session, mock_streamlit):
    mock_session.get.return_value.status_code = 401
    api.fetch_all_mood()
    mock_streamlit.switch_page.assert_called_once_with("pages/authorization.py")


def test_fetch_all_mood_server_error(mock_session, mock_streamlit):
    mock_session.get.return_value.status_code = 500
    api.fetch_all_mood()
    mock_streamlit.error.assert_called_once()
    mock_streamlit.stop.assert_called_once()


def test_fetch_create_mood_unauthorized(mock_session, mock_streamlit):
    mock_session.post.return_value.status_code = 401
    api.fetch_create_mood(date.today(), 3, "test")
    mock_streamlit.switch_page.assert_called_once_with("pages/authorization.py")


def test_fetch_create_mood_server_error(mock_session, mock_streamlit):
    mock_session.post.return_value.status_code = 500
    mock_session.post.return_value.text = "Something broke"
    result = api.fetch_create_mood(date.today(), 5, "note")
    assert result is False
    mock_streamlit.error.assert_called_once()


def test_fetch_delete_mood_unauthorized(mock_session, mock_streamlit):
    mock_session.delete.return_value.status_code = 401
    api.fetch_delete_mood("2024-01-01")
    mock_streamlit.switch_page.assert_called_once_with("pages/authorization.py")


def test_fetch_delete_mood_server_error(mock_session, mock_streamlit):
    mock_session.delete.return_value.status_code = 500
    api.fetch_delete_mood("2024-01-01")
    mock_streamlit.error.assert_called_once()
    mock_streamlit.stop.assert_called_once()


def test_fetch_edit_mood_unauthorized(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 401
    api.fetch_edit_mood("2024-01-01", value=1)
    mock_streamlit.switch_page.assert_called_once_with("pages/authorization.py")


def test_fetch_edit_mood_server_error(mock_session, mock_streamlit):
    mock_session.put.return_value.status_code = 500
    api.fetch_edit_mood("2024-01-01", note="updated")
    mock_streamlit.error.assert_called_once()
    mock_streamlit.stop.assert_called_once()