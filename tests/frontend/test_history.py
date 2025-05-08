import datetime
from unittest.mock import MagicMock

import pytest

from mood_diary.frontend.pages import history


@pytest.fixture
def mock_streamlit(mocker):
    mock_st = mocker.patch("mood_diary.frontend.pages.history.st")
    mock_st.session_state = MagicMock()
    return mock_st


@pytest.fixture
def sample_mood_data():
    return [
        {
            "date": datetime.date.today().isoformat(),
            "value": 7,
            "note": "Feeling good",
        },
        {
            "date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
            "value": 5,
            "note": "Meh",
        },
        {
            "date": (datetime.date.today() - datetime.timedelta(days=1)).isoformat(),
            "value": 1,
            "note": "yay",
        },
    ]


def test_display_empty_mood_history(mock_streamlit, mocker):
    mocker.patch("mood_diary.frontend.pages.history.fetch_all_mood", return_value=[])

    # Настроим возвращаемое значение для st.columns([3, 3, 2])
    mock_col1 = mocker.MagicMock()
    mock_col2 = mocker.MagicMock()
    mock_col3 = mocker.MagicMock()
    mock_streamlit.columns.return_value = [mock_col1, mock_col2, mock_col3]

    # Также подстрахуемся с date_input и selectbox
    mock_streamlit.date_input.side_effect = [
        datetime.date.today() - datetime.timedelta(days=30),
        datetime.date.today(),
    ]
    mock_streamlit.selectbox.return_value = None

    import mood_diary.frontend.pages.history as history
    history.display_mood_history()


def test_display_mood_history_with_data(mock_streamlit, sample_mood_data, mocker):
    fetch_mock = mocker.patch(
        "mood_diary.frontend.pages.history.fetch_all_mood",
        return_value=sample_mood_data,
    )
    mock_streamlit.date_input.side_effect = [
        datetime.date.today() - datetime.timedelta(days=30),
        datetime.date.today(),
    ]
    # Настроим возвращаемое значение для st.columns длиной в столько MagicMock сколько элементов в переданном списке
    mock_col1 = mocker.MagicMock()
    mock_col2 = mocker.MagicMock()
    mock_col3 = mocker.MagicMock()
    mock_col4 = mocker.MagicMock()
    mock_col5 = mocker.MagicMock()
    mock_streamlit.columns.return_value = [mock_col1, mock_col2, mock_col3, mock_col4, mock_col5]

    # Также подстрахуемся с date_input и selectbox
    mock_streamlit.date_input.side_effect = [
        datetime.date.today() - datetime.timedelta(days=30),
        datetime.date.today(),
    ]
    mock_streamlit.selectbox.return_value = None
    mock_streamlit.selectbox.return_value = None

    history.display_mood_history()

    assert fetch_mock.called
    assert isinstance(mock_streamlit.session_state.mood_data, list)
    assert len(mock_streamlit.session_state.mood_data) == 3


def test_display_mood_history_empty_list(mock_streamlit, mocker):
    mocker.patch("mood_diary.frontend.pages.history.fetch_all_mood", return_value=[])
    mock_streamlit.columns.return_value = [mocker.MagicMock() for _ in range(3)]
    mock_streamlit.date_input.side_effect = [
        datetime.date.today() - datetime.timedelta(days=30),
        datetime.date.today(),
    ]
    mock_streamlit.selectbox.return_value = None

    import mood_diary.frontend.pages.history as history
    history.display_mood_history()

    mock_streamlit.title.assert_called_once_with("Your Mood History")
    mock_streamlit.info.assert_called_once()  # показывает сообщение о пустой истории
