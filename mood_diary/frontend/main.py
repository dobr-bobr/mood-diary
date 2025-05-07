import datetime
from shared.helper.requests_session import provide_requests_session
import altair as alt
import pandas as pd
import streamlit as st

BASE_URL = "https://mood-diary.duckdns.org/api"
session = provide_requests_session()


def fetch_profile():
    try:
        response = session.get(f"{BASE_URL}/auth/profile")
        if response.status_code == 200:
            profile_data = response.json()
            st.session_state.name = profile_data.get("name", "User")
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error("Failed to load user profile")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching profile: {e}")
        st.stop()


fetch_profile()
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
}}
.rating-selected {{
    border: 3px solid white !important;
    box-shadow: 0 0 10px white !important;
}}
</style>
<div class="mood-banner">
    <h2>How do you feel today, {st.session_state.name}?</h2>
    <p>Please, mark your mood today</p>
</div>
""",
    unsafe_allow_html=True,
)


def fetch_all_mood(start_date, end_date, value=None):
    try:
        params = {"start_date": start_date, "end_date": end_date}
        if value is not None:
            params["value"] = value

        response = session.get(f"{BASE_URL}/mood", params=params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error(f"Failed to load user mood: {response.status_code}")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching mood: {e}")
        st.stop()


def fetch_create_mood(value, note):
    try:
        payload = {
            "date": datetime.date.today().isoformat(),
            "value": value,
            "note": note,
        }

        response = session.post(f"{BASE_URL}/mood", json=payload)

        if response.status_code == 200:
            st.success("Mood entry created successfully!")
            get_user_ratings_data.clear()
            return True
        elif response.status_code == 400:
            error_msg = response.json().get(
                "detail", "Mood for this date already exists"
            )
            st.warning(f"{error_msg}")
            return False
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error(
                f"Failed to create mood: {response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        st.error(f"Error creating mood: {e}")
        return False


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

            if "T" in date_str:
                date_obj = datetime.datetime.fromisoformat(date_str)
            else:
                date_obj = datetime.datetime.combine(
                    datetime.date.fromisoformat(date_str), datetime.time()
                )

            ratings.append(
                {"date": date_obj, "rating": value, "comment": note}
            )
        except Exception as e:
            print(f"Error processing entry: {entry}, error: {e}")
            continue

    return pd.DataFrame(ratings)


if "user_ratings_df" not in st.session_state:
    st.session_state.user_ratings_df = get_user_ratings_data()

if "form_comment" not in st.session_state:
    st.session_state.form_comment = ""
if "selected_rating" not in st.session_state:
    st.session_state.selected_rating = None

if not st.session_state.user_ratings_df.empty:
    user_ratings = st.session_state.user_ratings_df

    line = (
        alt.Chart(user_ratings)
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
        alt.Chart(user_ratings)
        .mark_circle(size=150)
        .encode(
            x="date:T",
            y="rating:Q",
            color=alt.Color(
                "rating:Q",
                scale=alt.Scale(
                    domain=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
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

    chart = (line + points).properties(height=300)
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
        key="comment_area",
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
        color = [
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
        ][i]

        with col:
            selected = st.session_state.selected_rating == rating_value
            st.markdown(
                f"""
                <style>
                div[data-testid="column"]:nth-of-type({i + 1}) button {{
                    background-color: {color} !important;
                    color: white !important;
                    border-radius: 20px !important;
                    width: 100% !important;
                    height: 40px !important;
                    margin: 2px 0 !important;
                    {'border: 3px solid white !important; box-shadow: 0 0 10px white !important;' if selected else ''}
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

            if st.form_submit_button(
                str(rating_value),
                help=f"Rating {rating_value}",
            ):
                st.session_state.selected_rating = rating_value
                st.session_state.rating_required = False

    submitted = st.form_submit_button("Submit")
    if submitted:
        if st.session_state.selected_rating is None:
            st.session_state.rating_required = True
            st.warning("Please select a rating")
        elif not comment.strip():
            st.warning("Please enter a comment")
        else:
            success = fetch_create_mood(
                st.session_state.selected_rating, comment
            )
            if success:
                st.session_state.form_comment = ""
                st.session_state.selected_rating = None
                st.session_state.user_ratings_df = get_user_ratings_data()
                st.rerun()
