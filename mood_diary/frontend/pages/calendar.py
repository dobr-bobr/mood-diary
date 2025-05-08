import datetime
import streamlit as st

from mood_diary.frontend.pages.history import get_rating_emoji
from mood_diary.frontend.shared.api.api import (
    fetch_mood_by_date,
    fetch_edit_mood,
    fetch_delete_mood,
)


def calendar_page():
    st.title("Mood Calendar")

    selected_date = st.date_input(
        "Select a date",
        value=datetime.date.today(),
        min_value=datetime.date.today() - datetime.timedelta(days=365),
        max_value=datetime.date.today(),
    )

    deleted_key = f"deleted_{selected_date.isoformat()}"
    if deleted_key in st.session_state and st.session_state[deleted_key]:
        st.info("No mood entry for this day.")
        return

    mood_entry = fetch_mood_by_date(selected_date.isoformat())

    if not mood_entry:
        return

    rating = mood_entry.get("value")
    note = mood_entry.get("note", "")

    st.markdown(f"### {selected_date.strftime('%B %d, %Y')}")
    st.markdown(f"**Mood:** {get_rating_emoji(rating)} {rating}")

    with st.form("edit_mood_form", clear_on_submit=False):
        new_rating = st.selectbox(
            "Edit mood rating",
            options=list(range(1, 11)),
            index=rating - 1,
            format_func=lambda x: f"{get_rating_emoji(x)} {x}",
        )
        new_note = st.text_area("Edit your note", value=note, height=100)
        col1, col2 = st.columns([2, 1])
        with col1:
            save = st.form_submit_button("Save changes")
        with col2:
            delete = st.form_submit_button("Delete entry", type="secondary")

        if save:
            if fetch_edit_mood(
                selected_date.isoformat(), value=new_rating, note=new_note
            ):
                st.success("Mood entry updated!")
                st.rerun()
        if delete:
            if fetch_delete_mood(selected_date.isoformat()):
                st.success("Mood entry deleted!")
                st.session_state[deleted_key] = True
                st.rerun()


calendar_page()
