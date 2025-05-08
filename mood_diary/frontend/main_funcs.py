import datetime

import altair as alt
import pandas as pd
import streamlit as st

from mood_diary.frontend.shared.api.api import (
    fetch_all_mood,
)


def create_mood_chart(df):
    line = (
        alt.Chart(df)
        .mark_line(interpolate="monotone", strokeWidth=3)
        .encode(
            x=alt.X("date:T", title="Date"),
            y=alt.Y(
                "rating:Q",
                title="Mood Rating",
                scale=alt.Scale(domain=[0, 11]),
            ),
            color=alt.value("#888888"),
        )
    )

    points = (
        alt.Chart(df)
        .mark_circle(size=150)
        .encode(
            x="date:T",
            y="rating:Q",
            color=alt.Color(
                "rating:Q",
                scale=alt.Scale(
                    domain=list(range(1, 11)),
                    range=[
                        "#ef4056",
                        "#f47d2f",
                        "#f8c13a",
                        "#c0d23e",
                        "#8dc63f",
                        "#53a78c",
                        "#3e83c3",
                        "#5465b3",
                        "#6247aa",
                        "#4a357f",
                    ],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date", format="%Y-%m-%d"),
                alt.Tooltip("rating:Q", title="Rating"),
                alt.Tooltip("comment:N", title="Comment"),
            ],
        )
    )

    return (line + points).properties(height=300)


def refresh_data():
    st.session_state.user_ratings_df = get_user_ratings_data()
    st.session_state.mood_data = fetch_all_mood()
    st.session_state.needs_refresh = False


def get_user_ratings_data():
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=30)
    mood_data = fetch_all_mood(start_date.isoformat(), end_date.isoformat())

    if not mood_data:
        return pd.DataFrame(columns=["date", "rating", "comment"])

    ratings = []
    for entry in mood_data:
        try:
            date_str = entry.get("date")
            value = entry.get("value")
            note = entry.get("note", "")

            date_obj = (
                datetime.datetime.fromisoformat(date_str)
                if "T" in date_str
                else datetime.datetime.combine(
                    datetime.date.fromisoformat(date_str), datetime.time()
                )
            )

            ratings.append(
                {"date": date_obj, "rating": value, "comment": note}
            )
        except Exception as e:
            print(f"Error processing entry: {entry}, error: {e}")

    return pd.DataFrame(ratings)
