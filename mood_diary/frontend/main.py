import datetime

import streamlit as st

from mood_diary.frontend.main_funcs import refresh_data, create_mood_chart
from mood_diary.frontend.pages.history import get_rating_emoji
from mood_diary.frontend.shared.api.api import (
    fetch_profile,
    fetch_create_mood,
)

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
