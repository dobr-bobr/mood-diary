import datetime
from shared.helper.requests_session import provide_requests_session
import pandas as pd
import streamlit as st

from mood_diary.frontend.main import fetch_all_mood

BASE_URL = "https://mood-diary.duckdns.org/api"
session = provide_requests_session()


def display_mood_history():
    st.title("Your Mood History")
    mood_data = fetch_all_mood()
    if not mood_data:
        st.info("No mood entries found")
        return

    history = []
    for entry in mood_data:
        try:
            date_str = entry.get("date")
            value = entry.get("value")
            note = entry.get("note", "")

            if "T" in date_str:
                date_obj = datetime.datetime.fromisoformat(date_str).date()
            else:
                date_obj = datetime.date.fromisoformat(date_str)

            history.append({
                "Date": date_obj,
                "Rating": value,
                "Note": note
            })
        except Exception as e:
            print(f"Error processing entry: {entry}, error: {e}")
            continue

    df = pd.DataFrame(history)
    df.sort_values("Date", ascending=False, inplace=True)

    st.dataframe(
        df,
        column_config={
            "Date": st.column_config.DateColumn("Date"),
            "Rating": st.column_config.NumberColumn("Rating", format="%d ⭐"),
            "Note": st.column_config.TextColumn("Note")
        },
        use_container_width=True,
        hide_index=True
    )


display_mood_history()

if st.button("Back to Mood Tracker"):
    st.switch_page("main.py")