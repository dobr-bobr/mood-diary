import time

import streamlit as st
from shared.helper.check_passwords import compare_passwords  # type: ignore[import-not-found]

from shared.helper.requests_session import provide_requests_session  # type: ignore[import-not-found]

st.set_page_config(
    page_title="Registration",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def register():
    payload = {
        "username": st.session_state.username,
        "password": st.session_state.password,
        "name": st.session_state.name,
    }

    try:
        session = provide_requests_session()
        response = session.post(
            "https://mood-diary.duckdns.org/api/auth/register", json=payload
        )
        data = response.json()

        if response.status_code == 200:
            st.success("Account has been successfully created")

        if response.status_code == 400:
            raise Exception(data["detail"])
        elif response.status_code == 422:
            raise Exception(
                f"{data['detail'][0]['loc'][1].capitalize()}: {data['detail'][0]['msg'].lower()}"
            )
    except Exception as e:
        st.error(f"{e}")


with st.form("my_form", enter_to_submit=False):
    username = st.text_input("Username", key="username")
    password = st.text_input("Password", key="password", type="password")
    confirm_password = st.text_input(
        "Confirm password", key="confirm_password", type="password"
    )
    name = st.text_input("Name", key="name")

    is_submitted = st.form_submit_button("Register")

    auth_link = st.form_submit_button(
        "Have an account?", help="Redirect to Login page", type="secondary"
    )

    if (
        not compare_passwords(password, confirm_password)
        and len(password) > 0
        and len(confirm_password) > 0
    ):
        st.error("Password and confirm password should be the same")

    if auth_link:
        st.switch_page("pages/authorization.py")

    if is_submitted:
        if username and password and confirm_password:
            if compare_passwords(password, confirm_password):
                register()
                time.sleep(1)
                st.switch_page("main.py")
            else:
                st.error("Password and confirm password should be the same")
        else:
            st.error("All fields must be filled in")
