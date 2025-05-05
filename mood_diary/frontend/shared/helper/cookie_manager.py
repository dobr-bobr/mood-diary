import streamlit as st
import extra_streamlit_components as stx


@st.fragment
def get_cookie_manager():
    return stx.CookieManager()
