import streamlit as st
import requests
import extra_streamlit_components as stx
from datetime import datetime, timedelta

st.set_page_config(page_title="Registration", layout="centered", initial_sidebar_state="collapsed")

cookie_manager = stx.CookieManager()

def login():
    payload = {
      "username": st.session_state.username,
      "password": st.session_state.password
    }

    try:
        response = requests.post("https://mood-diary.duckdns.org/api/auth/login", json=payload)
        data = response.json()
        if response.status_code == 401:
            raise Exception(data['detail'])
        elif response.status_code == 422:
            raise Exception(f"{data['detail'][0]['loc'][1].capitalize()}: {data['detail'][0]['msg'].lower()}")
        
        return data
    except Exception as e:
        st.error(f"{e}")

with st.form("my_form", enter_to_submit=False):
    username = st.text_input('Username', key="username")
    password = st.text_input('Password', key="password", type="password")

    is_submited = st.form_submit_button('Sign in')

    auth_link = st.form_submit_button("Don't have an account?", help="Redirect to Sign In page", 
                                         type="secondary")

    if auth_link:
        st.switch_page('pages/registration.py')

    if is_submited:
        if username and password:
            tokens = login()

            # TODO: Solve problem with tokens, by some reason tokens are not saved in cookies
            access_expires = datetime.now() + timedelta(hours=1)
            cookie_manager.set('access', tokens['access_token'], expires_at=access_expires, key="access")
            refresh_expires = datetime.now() + timedelta(days=30)
            cookie_manager.set('refresh', tokens['refresh_token'], expires_at=refresh_expires, key="refresh")

            st.switch_page('main.py')
        else:
            st.error("All fields must be filled in")
