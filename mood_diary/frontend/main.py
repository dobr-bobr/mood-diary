import streamlit as st
import requests
import extra_streamlit_components as stx

cookie_manager = stx.CookieManager()
cookies = cookie_manager.get_all()

try:
    st.write(cookies);
    ACCESS_TOKEN = cookies.get('access')

    if not ACCESS_TOKEN:
        raise Exception()
except Exception:
    st.switch_page('pages/authorization.py')

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
    
