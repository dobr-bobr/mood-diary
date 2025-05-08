import datetime
import pandas as pd
import streamlit as st
from mood_diary.frontend.shared.api.api import fetch_all_mood, fetch_delete_mood


def display_mood_history():
    st.title("Your Mood History")
    st.session_state.mood_data = fetch_all_mood()

    if not st.session_state.mood_data:
        st.info("No mood entries found")
        return

    history = []
    for entry in st.session_state.mood_data:
        try:
            date_str = entry.get("date")
            value = entry.get("value")
            note = entry.get("note", "")

            date_obj = (datetime.datetime.fromisoformat(date_str).date() if "T" in date_str
                        else datetime.date.fromisoformat(date_str))

            history.append({
                "Date": date_obj,
                "Rating": value,
                "Note": note,
                "Delete": date_obj
            })
        except Exception as e:
            print(f"Error processing entry: {entry}, error: {e}")

    df = pd.DataFrame(history).sort_values("Date", ascending=False)

    for index, row in df.iterrows():
        cols = st.columns([3, 1, 6, 2])
        cols[0].write(row["Date"])
        cols[1].write(f"{row['Rating']} ⭐")
        cols[2].write(row["Note"])

        if cols[3].button("Delete", key=f"delete_{index}"):
            if fetch_delete_mood(row["Date"]):
                st.session_state.needs_refresh = True
                st.session_state.mood_data = fetch_all_mood()
                st.rerun()


display_mood_history()

if st.button("Back to Mood Tracker"):
    st.switch_page("main.py")