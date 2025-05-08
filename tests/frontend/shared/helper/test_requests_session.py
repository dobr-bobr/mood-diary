import requests
from mood_diary.frontend.shared.helper.requests_session import provide_requests_session
from unittest.mock import MagicMock

PATCH_TARGET_SESSION_STATE = 'mood_diary.frontend.shared.helper.requests_session.st.session_state'


def test_provide_requests_session_creates_new_session(mocker):
    mock_session_state = mocker.patch(PATCH_TARGET_SESSION_STATE)
    mock_requests_session_constructor = mocker.patch('requests.Session')

    session = provide_requests_session()

    mock_requests_session_constructor.assert_called_once_with()

    assert session is not None
    assert session is mock_requests_session_constructor.return_value


def test_provide_requests_session_returns_existing_session(mocker):
    mock_session_state = mocker.patch(PATCH_TARGET_SESSION_STATE)
    mock_session_state.__contains__.side_effect = lambda key: key == 'requests_session'

    mock_existing_session = MagicMock(spec=requests.Session)
    mock_session_state.requests_session = mock_existing_session

    mock_requests_session_constructor = mocker.patch('requests.Session')

    session = provide_requests_session()

    mock_requests_session_constructor.assert_not_called()

    assert session is not None
    assert session is mock_existing_session
