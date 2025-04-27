import streamlit as st
import requests
import extra_streamlit_components as stx

from shared.helper.cookie_manager import get_cookie_manager

cookie_manager = get_cookie_manager()

ACCESS_TOKEN = cookie_manager.get_all(key="auth_get_all").get("access")

if not ACCESS_TOKEN:
    st.switch_page('pages/authorization.py')
    st.stop()

st.title("Hello!")

def get_profile():
    try:
        st.write(ACCESS_TOKEN)
        response = requests.get(f"https://mood-diary.duckdns.org/api/auth/profile?authorization={ACCESS_TOKEN}")

        return response.json();
    except Exception as e:
        st.error(f"{e}")

if st.button("Test data"):
    data = get_profile()

    st.write(data)
    
