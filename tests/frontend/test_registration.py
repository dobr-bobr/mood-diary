from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_streamlit(mocker):
    st = mocker.patch("mood_diary.frontend.pages.registration.st")
    st.session_state = MagicMock()
    st.session_state.username = "testuser"
    st.session_state.password = "<PASSWORD>"
    st.session_state.confirm_password = "<PASSWORD>"
    st.session_state.name = "Test User"
    st.text_input.side_effect = lambda label, **kwargs: st.session_state[kwargs["key"]]
    st.form_submit_button.side_effect = [False, False]  # default: no button clicked
    return st


@pytest.fixture
def mock_requests_session(mocker):
    return mocker.patch("mood_diary.frontend.pages.registration.provide_requests_session")


def test_successful_registration(mocker, mock_streamlit, mock_requests_session):
    # Setup
    mock_streamlit.form_submit_button.side_effect = [True, False]  # Register clicked

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {}
    mock_requests_session.return_value.post.return_value = mock_resp

    switch_mock = mock_streamlit.switch_page

    # Import and run
    import mood_diary.frontend.pages.registration as reg
    reg.register()

    mock_streamlit.success.assert_called_with("Account has been successfully created")


def test_register_validation_error(mocker, mock_streamlit, mock_requests_session):
    mock_streamlit.form_submit_button.side_effect = [True, False]

    mock_resp = MagicMock()
    mock_resp.status_code = 422
    mock_resp.json.return_value = {
        "detail": [
            {"loc": ["body", "username"], "msg": "field required"}
        ]
    }
    mock_requests_session.return_value.post.return_value = mock_resp

    import mood_diary.frontend.pages.registration as reg
    reg.register()

    mock_streamlit.error.assert_called_with("Username: field required")


def test_register_user_already_exists(mocker, mock_streamlit, mock_requests_session):
    mock_streamlit.form_submit_button.side_effect = [True, False]

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"detail": "User already exists"}
    mock_requests_session.return_value.post.return_value = mock_resp

    import mood_diary.frontend.pages.registration as reg
    reg.register()

    mock_streamlit.error.assert_called_with("User already exists")
