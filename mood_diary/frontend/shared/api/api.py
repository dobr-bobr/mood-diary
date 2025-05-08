from mood_diary.frontend.shared.helper.requests_session import (
    provide_requests_session,
)
import streamlit as st

BASE_URL = "https://mood-diary.duckdns.org/api"


def fetch_profile():
    try:
        session = provide_requests_session()
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


def fetch_change_name(name):
    try:
        session = provide_requests_session()
        response = session.put(f"{BASE_URL}/auth/profile", json={"name": name})
        if response.status_code == 200:
            profile_data = response.json()
            st.session_state.name = profile_data.get("name", "User")
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error("Failed to change name")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching change name: {e}")
        st.stop()


def fetch_change_password(old_password, new_password):
    try:
        session = provide_requests_session()
        params = {
            "old_password": old_password,
            "new_password": new_password,
        }
        response = session.put(f"{BASE_URL}/auth/password", json=params)
        if response.status_code == 401:
            st.switch_page("pages/authorization.py")
        elif response.status_code == 200:
            st.info("Password successfully changed")
            st.switch_page("main.py")
        else:
            st.error(
                f"Failed to change password "
                f"{response.status_code, response.text}"
            )
            st.stop()
    except Exception as e:
        st.error(f"Error fetching change password: {e}")
        st.stop()


def fetch_mood_by_date(date):
    try:
        session = provide_requests_session()
        response = session.get(f"{BASE_URL}/mood/{date}")
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            st.info("No mood entry for this day.")
            return None
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error(f"Failed to get user mood: {response.status_code}")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching mood: {e}")
        st.stop()


def fetch_all_mood(start_date=None, end_date=None, value=None):
    try:
        session = provide_requests_session()
        params = {}
        if value is not None:
            params["value"] = value
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date

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


def fetch_create_mood(date, value, note):
    try:
        session = provide_requests_session()
        payload = {
            "date": date.isoformat(),
            "value": value,
            "note": note,
        }

        response = session.post(f"{BASE_URL}/mood", json=payload)

        if response.status_code == 200:
            st.success("Mood entry created successfully!")
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
                f"Failed to create mood: "
                f"{response.status_code} - {response.text}"
            )
            return False
    except Exception as e:
        st.error(f"Error creating mood: {e}")
        return False


def fetch_delete_mood(date):
    try:
        session = provide_requests_session()
        response = session.delete(f"{BASE_URL}/mood/{date}")

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error(f"Failed to delete user mood: {response.status_code}")
            st.stop()
    except Exception as e:
        st.error(f"Error fetching mood: {e}")
        st.stop()


def fetch_edit_mood(date, value=None, note=None):
    try:
        params = {}
        if value is not None:
            params["value"] = value
        if note is not None:
            params["note"] = note

        session = provide_requests_session()
        response = session.put(f"{BASE_URL}/mood/{date}", json=params)

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            st.switch_page("pages/authorization.py")
        else:
            st.error(f"Failed to edit user mood: {response.status_code}")
            st.stop()
    except Exception as e:
        st.error(f"Error editing mood: {e}")
        st.stop()
