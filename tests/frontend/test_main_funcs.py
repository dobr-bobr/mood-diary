import datetime
from unittest.mock import patch, MagicMock

import altair as alt
import pandas as pd
import pytest

from mood_diary.frontend import main_funcs


@pytest.fixture
def mock_streamlit_session_state():
    with patch("mood_diary.frontend.main_funcs.st") as mock_st:
        mock_st.session_state = MagicMock()
        yield mock_st


@patch("mood_diary.frontend.main_funcs.fetch_all_mood")
def test_get_user_ratings_data_valid(mock_fetch):
    mock_fetch.return_value = [
        {"date": "2024-05-01", "value": 7, "note": "Good"},
        {"date": "2024-05-02T10:30:00", "value": 8, "note": ""},
    ]

    df = main_funcs.get_user_ratings_data()

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ["date", "rating", "comment"]
    assert df.iloc[0]["rating"] == 7
    assert df.iloc[0]["comment"] == "Good"
    assert isinstance(df.iloc[0]["date"], datetime.datetime)


@patch("mood_diary.frontend.main_funcs.fetch_all_mood")
def test_get_user_ratings_data_empty(mock_fetch):
    mock_fetch.return_value = []

    df = main_funcs.get_user_ratings_data()
    assert df.empty
    assert list(df.columns) == ["date", "rating", "comment"]


@patch("mood_diary.frontend.main_funcs.fetch_all_mood")
def test_get_user_ratings_data_invalid_entry(mock_fetch):
    mock_fetch.return_value = [
        {"date": "bad-date", "value": 5, "note": "oops"}
    ]

    df = main_funcs.get_user_ratings_data()
    assert df.empty  # error in date parsing should skip the entry


@patch("mood_diary.frontend.main_funcs.fetch_all_mood")
def test_refresh_data(mock_fetch, mock_streamlit_session_state):
    mock_fetch.return_value = [
        {"date": "2024-05-01", "value": 6, "note": "okay"}
    ]

    main_funcs.refresh_data()

    assert (
        mock_streamlit_session_state.session_state.user_ratings_df is not None
    )
    assert mock_streamlit_session_state.session_state.mood_data is not None
    assert mock_streamlit_session_state.session_state.needs_refresh is False


def test_create_mood_chart_returns_chart():
    df = pd.DataFrame(
        [
            {
                "date": datetime.datetime(2024, 5, 1),
                "rating": 5,
                "comment": "ok",
            },
            {
                "date": datetime.datetime(2024, 5, 2),
                "rating": 7,
                "comment": "good",
            },
        ]
    )

    chart = main_funcs.create_mood_chart(df)
    assert isinstance(chart, alt.Chart) or hasattr(
        chart, "to_json"
    )  # VegaLiteChart
