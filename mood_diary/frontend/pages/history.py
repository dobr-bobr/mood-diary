import datetime
import pandas as pd
import streamlit as st
from mood_diary.frontend.shared.api.api import (
    fetch_all_mood,
    fetch_delete_mood,
    fetch_edit_mood,
)


def get_rating_emoji(rating):
    rating_emojis = {
        1: "🔴",
        2: "🟠",
        3: "🟡",
        4: "🟡",
        5: "🟢",
        6: "🟢",
        7: "🔵",
        8: "🔵",
        9: "🟣",
        10: "🟣",
    }
    return rating_emojis.get(rating, "⭐")


def display_mood_history():
    st.title("Your Mood History")

    col1, col2, col3 = st.columns([3, 3, 2])[:3]
    with col1:
        start_date = st.date_input(
            "Start date",
            value=datetime.date.today() - datetime.timedelta(days=30),
            key="filter_start_date",
        )
    with col2:
        end_date = st.date_input(
            "End date", value=datetime.date.today(), key="filter_end_date"
        )
    with col3:
        rating_filter = st.selectbox(
            "Rating",
            options=[None] + list(range(1, 11)),
            format_func=lambda x: (
                "All" if x is None else f"{get_rating_emoji(x)} {x}"
            ),
            index=0,
            key="filter_rating",
        )

    st.markdown(
        """
    <style>
    .mood-history-container {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        background-color: #f9f9fb;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .mood-date {
        font-weight: bold;
        color: #2c4a3a;
        font-size: 15px;
        margin-bottom: 6px;
    }
    .mood-rating {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 18px;
        margin-bottom: 6px;
    }
    .mood-note textarea {
        width: 100% !important;
        min-height: 60px !important;
        max-height: 90px !important;
        font-size: 14px !important;
        padding: 7px !important;
        border-radius: 7px !important;
        border: 1px solid #b0b0b0 !important;
        resize: vertical !important;
        background: #fff !important;
        color: #222 !important;
    }
    .mood-actions {
        display: flex;
        gap: 10px;
        justify-content: flex-end;
    }
    .stButton>button {
        border-radius: 7px !important;
        font-size: 16px !important;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    start_date_str = start_date.isoformat() if start_date else None
    end_date_str = end_date.isoformat() if end_date else None
    mood_data = fetch_all_mood(
        start_date=start_date_str, end_date=end_date_str, value=rating_filter
    )
    st.session_state.mood_data = mood_data

    if not mood_data:
        st.info("No mood entries found")
        return

    history = []
    for entry in mood_data:
        try:
            date_str = entry.get("date")
            value = entry.get("value")
            note = entry.get("note", "")
            date_obj = (
                datetime.datetime.fromisoformat(date_str).date()
                if "T" in date_str
                else datetime.date.fromisoformat(date_str)
            )
            history.append(
                {
                    "Date": date_obj,
                    "Rating": value,
                    "Note": note,
                }
            )
        except Exception as e:
            print(f"Error processing entry: {entry}, error: {e}")

    df = pd.DataFrame(history).sort_values("Date", ascending=False)

    for index, row in df.iterrows():
        with st.container():
            cols = st.columns([2, 1, 5, 2])

            with cols[0]:
                st.markdown(
                    f'<div class="mood-date">{row["Date"]}</div>',
                    unsafe_allow_html=True,
                )

            with cols[1]:
                rating = st.selectbox(
                    "Rating",
                    options=list(range(1, 11)),
                    index=row["Rating"] - 1,
                    key=f"rating_edit_{index}",
                    label_visibility="collapsed",
                )
                st.markdown(
                    f'<div class="mood-rating">'
                    f"{get_rating_emoji(rating)} {rating}</div>",
                    unsafe_allow_html=True,
                )

            with cols[2]:
                note = st.text_area(
                    "Note",
                    value=row["Note"],
                    key=f"note_edit_{index}",
                    height=80,
                    label_visibility="collapsed",
                    placeholder="Enter your notes here...",
                    max_chars=500,
                )
                st.markdown(
                    '<div class="mood-note"></div>', unsafe_allow_html=True
                )

            with cols[3]:
                st.markdown(
                    '<div class="mood-actions">', unsafe_allow_html=True
                )
                save_col, delete_col = st.columns(2)[:2]
                with save_col:
                    if st.button(
                        "💾",
                        key=f"save_{index}",
                        help="Save changes",
                        use_container_width=True,
                    ):
                        if fetch_edit_mood(
                            row["Date"].isoformat(), value=rating, note=note
                        ):
                            st.session_state.mood_data = fetch_all_mood(
                                start_date=start_date_str,
                                end_date=end_date_str,
                                value=rating_filter,
                            )
                            st.rerun()
                with delete_col:
                    if st.button(
                        "🗑️",
                        key=f"delete_{index}",
                        help="Delete entry",
                        use_container_width=True,
                    ):
                        if fetch_delete_mood(row["Date"]):
                            st.session_state.needs_refresh = True
                            st.session_state.mood_data = fetch_all_mood(
                                start_date=start_date_str,
                                end_date=end_date_str,
                                value=rating_filter,
                            )
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")


display_mood_history()

if st.button("Back"):
    st.switch_page("main.py")
