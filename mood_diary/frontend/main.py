import datetime
from mood_diary.frontend.pages.history import get_rating_emoji
from mood_diary.frontend.shared.api.api import (
    fetch_profile,
    fetch_all_mood,
    fetch_create_mood,
)
import altair as alt
import pandas as pd
import streamlit as st


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


fetch_profile()

if "user_ratings_df" not in st.session_state or st.session_state.get(
    "needs_refresh", False
):
    refresh_data()
if "form_comment" not in st.session_state:
    st.session_state.form_comment = ""
if "selected_rating" not in st.session_state:
    st.session_state.selected_rating = None
if "selected_date" not in st.session_state:
    st.session_state.selected_date = datetime.date.today()

st.markdown(
    f"""
<style>
.mood-banner {{
    background: linear-gradient(90deg, #1e3b29, #2c4a3a);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin-bottom: 20px;
}}
.rating-btn {{
    width: 100% !important;
    height: 40px !important;
    margin: 2px 0 !important;
    border: none !important;
    color: white !important;
    border-radius: 20px !important;
}}
.rating-selected {{
    border: 3px solid white !important;
    box-shadow: 0 0 10px white !important;
}}
.date-picker {{
    margin: 15px 0;
}}
</style>
<div class="mood-banner">
    <h2>How do you feel today, {st.session_state.name}?</h2>
    <p>Please, mark your mood today</p>
</div>
""",
    unsafe_allow_html=True,
)

if not st.session_state.user_ratings_df.empty:
    user_ratings = st.session_state.user_ratings_df
    chart = create_mood_chart(user_ratings)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info(
        "No mood ratings data available yet. Start tracking your mood below!"
    )

with st.form(key="comment_form", clear_on_submit=False, enter_to_submit=False):
    comment = st.text_area(
        "Your thoughts",
        value=st.session_state.form_comment,
        placeholder="Type your thoughts here...",
        height=100,
    )
    st.session_state.form_comment = comment

    if st.session_state.get("rating_required", False):
        st.markdown(
            "<p class='rating-required'>Please select a rating</p>",
            unsafe_allow_html=True,
        )

    rating_cols = st.columns(10)
    for i, col in enumerate(rating_cols):
        rating_value = i + 1
        emoji = get_rating_emoji(rating_value)

        with col:
            selected = st.session_state.selected_rating == rating_value
            button_style = f"""
            <style>
            div[data-testid="stForm"] div[data-testid="column"]:nth-of-type({i + 1}) button {{
                {"border: 3px solid white !important;" if selected else ""}
                {"box-shadow: 0 0 10px white !important;" if selected else ""}
            }}
            </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)

            if st.form_submit_button(f"{rating_value} {emoji}"):
                st.session_state.selected_rating = rating_value
                st.session_state.rating_required = False

    st.markdown('<div class="date-picker">', unsafe_allow_html=True)
    selected_date = st.date_input(
        "Select date",
        value=st.session_state.selected_date,
        min_value=datetime.date.today() - datetime.timedelta(days=36500),
        max_value=datetime.date.today(),
    )
    st.session_state.selected_date = selected_date
    st.markdown("</div>", unsafe_allow_html=True)

    submitted = st.form_submit_button("Submit")
    if submitted:
        if st.session_state.selected_rating is None:
            st.session_state.rating_required = True
            st.warning("Please select a rating")
        else:
            if fetch_create_mood(
                st.session_state.selected_date,
                st.session_state.selected_rating,
                comment,
            ):
                st.session_state.form_comment = ""
                st.session_state.selected_rating = None
                refresh_data()
                st.rerun()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("View Full Mood History"):
        st.session_state.needs_refresh = True
        st.switch_page("pages/history.py")

with col2:
    if st.button("View Calendar"):
        st.session_state.needs_refresh = True
        st.switch_page("pages/calendar.py")

with col3:
    if st.button("View your profile"):
        st.switch_page("pages/profile.py")
