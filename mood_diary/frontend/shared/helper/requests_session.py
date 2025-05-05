import requests
import streamlit as st


def provide_requests_session():
    if "requests_session" not in st.session_state:
        st.session_state.requests_session = requests.Session()

    return st.session_state.requests_session
