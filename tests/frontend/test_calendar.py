import datetime
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def today():
    return datetime.date(2025, 5, 8)


@pytest.fixture
def mock_streamlit(mocker, today):
    mock_st = mocker.patch("mood_diary.frontend.pages.calendar.st")
    mock_st.date_input.return_value = today
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.selectbox.return_value = 5
    mock_st.text_area.return_value = "Updated note"
    mock_st.form_submit_button.side_effect = [False, False]  # Default: no save, no delete
    return mock_st


@pytest.fixture
def sample_entry():
    return {
        "value": 5,
        "note": "Felt okay",
    }


def test_no_entry_found(mocker, mock_streamlit, today):
    mocker.patch("mood_diary.frontend.pages.calendar.fetch_mood_by_date", return_value=None)

    from mood_diary.frontend.pages.calendar import calendar_page
    calendar_page()

    mock_streamlit.markdown.assert_not_called()


def test_entry_displayed(mocker, mock_streamlit, today, sample_entry):
    mocker.patch("mood_diary.frontend.pages.calendar.fetch_mood_by_date", return_value=sample_entry)
    mocker.patch("mood_diary.frontend.pages.calendar.get_rating_emoji", return_value="🙂")

    from mood_diary.frontend.pages.calendar import calendar_page
    calendar_page()

    mock_streamlit.markdown.assert_any_call("### May 08, 2025")
    mock_streamlit.markdown.assert_any_call("**Mood:** 🙂 5")


def test_save_mood_changes(mocker, mock_streamlit, today, sample_entry):
    mocker.patch("mood_diary.frontend.pages.calendar.fetch_mood_by_date", return_value=sample_entry)
    mocker.patch("mood_diary.frontend.pages.calendar.get_rating_emoji", return_value="🙂")
    edit_mock = mocker.patch("mood_diary.frontend.pages.calendar.fetch_edit_mood", return_value=True)

    mock_streamlit.form_submit_button.side_effect = [True, False]  # save pressed
    rerun = mocker.patch("mood_diary.frontend.pages.calendar.st.rerun")

    from mood_diary.frontend.pages.calendar import calendar_page
    calendar_page()

    edit_mock.assert_called_once_with("2025-05-08", value=5, note="Updated note")
    mock_streamlit.success.assert_called_with("Mood entry updated!")
    rerun.assert_called_once()


def test_delete_mood_entry(mocker, mock_streamlit, today, sample_entry):
    mocker.patch("mood_diary.frontend.pages.calendar.fetch_mood_by_date", return_value=sample_entry)
    mocker.patch("mood_diary.frontend.pages.calendar.get_rating_emoji", return_value="😐")
    delete_mock = mocker.patch("mood_diary.frontend.pages.calendar.fetch_delete_mood", return_value=True)
    rerun = mocker.patch("mood_diary.frontend.pages.calendar.st.rerun")

    mock_streamlit.form_submit_button.side_effect = [False, True]  # delete pressed
    from mood_diary.frontend.pages.calendar import calendar_page
    calendar_page()

    delete_mock.assert_called_once_with("2025-05-08")
    mock_streamlit.success.assert_called_with("Mood entry deleted!")
    rerun.assert_called_once()


def test_deleted_entry_shows_info(mocker, mock_streamlit, today):
    mock_streamlit.session_state["deleted_2025-05-08"] = True

    from mood_diary.frontend.pages.calendar import calendar_page
    calendar_page()
