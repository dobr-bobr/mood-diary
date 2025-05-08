import datetime
from mood_diary.frontend.shared.api.api import fetch_all_mood, fetch_delete_mood
import pandas as pd
import streamlit as st

def display_mood_history():
    st.title("Your Mood History")

    if "mood_data" not in st.session_state:
        st.session_state.mood_data = fetch_all_mood()

    if not st.session_state.mood_data:
        st.info("No mood entries found")

    history = []
    for entry in st.session_state.mood_data:
        try:
            date_str = entry.get("date")
            value = entry.get("value")
            note = entry.get("note", "")

            if "T" in date_str:
                date_obj = datetime.datetime.fromisoformat(date_str).date()
            else:
                date_obj = datetime.date.fromisoformat(date_str)

            history.append(
                {
                    "Date": date_obj,
                    "Rating": value,
                    "Note": note,
                    "Delete": date_obj,
                }
            )
        except Exception as e:
            print(f"Error processing entry: {entry}, error: {e}")
            continue

    df = pd.DataFrame(history)
    df.sort_values("Date", ascending=False, inplace=True)

    df_with_actions = df.copy()
    df_with_actions["Action"] = ""

    for index, row in df.iterrows():
        cols = st.columns([3, 1, 6, 2])
        cols[0].write(row["Date"])
        cols[1].write(f"{row['Rating']} ⭐")
        cols[2].write(row["Note"])

        if cols[3].button("Delete", key=f"delete_{index}"):
            if fetch_delete_mood(row["Date"]):
                st.session_state.mood_data = fetch_all_mood()
                st.rerun()

    if st.button("Back to Mood Tracker"):
        st.switch_page("main.py")

display_mood_history()
