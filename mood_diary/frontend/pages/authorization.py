import streamlit as st
from shared.helper.requests_session import provide_requests_session

st.set_page_config(
    page_title="Authorization",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def clear_user_data():
    preserved_keys = ['username', 'password', 'access_token']

    all_keys = list(st.session_state.keys())

    for key in all_keys:
        if key not in preserved_keys:
            del st.session_state[key]


def login():
    payload = {
        "username": st.session_state.username,
        "password": st.session_state.password,
    }

    try:
        clear_user_data()
        session = provide_requests_session()
        response = session.post(
            "https://mood-diary.duckdns.org/api/auth/login", json=payload
        )

        if response.status_code == 200:
            st.switch_page("main.py")

        data = response.json()

        if response.status_code == 401:
            raise Exception(data["detail"])
        elif response.status_code == 422:
            raise Exception(
                f"{data['detail'][0]['loc'][1].capitalize()}: {data['detail'][0]['msg'].lower()}"
            )
        return data
    except Exception as e:
        st.error(f"{e}")
        return None


with st.form("my_form", enter_to_submit=False):
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", key="password", type="password")

    is_submitted = st.form_submit_button("Sign in")
    auth_link = st.form_submit_button(
        "Don't have an account?",
        help="Redirect to Sign In page",
        type="secondary",
    )

    if auth_link:
        st.switch_page("pages/registration.py")

    if is_submitted:
        if username and password:
            tokens = login()
        else:
            st.error("All fields must be filled in")
