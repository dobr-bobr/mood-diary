import streamlit as st

from mood_diary.frontend.shared.api.api import fetch_change_password, fetch_change_name

st.markdown(
    """
    <style>
    .profile-section {
        background: #f8f9fa;
        padding: 30px 30px 15px 30px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("👤 Profile Settings")

with st.container():
    st.subheader("Change your name")

    with st.form("change_name_form", clear_on_submit=False):
        new_name = st.text_input("Your name", value=st.session_state.get("name", "User"), max_chars=32)
        submitted_name = st.form_submit_button("Change name")
        if submitted_name:
            if not new_name.strip():
                st.warning("Name cannot be empty.")
            else:
                fetch_change_name(new_name)
                st.success("Name changed successfully!")

    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.subheader("Change your password")

    with st.form("change_password_form", clear_on_submit=True):
        old_password = st.text_input("Current password", type="password")
        new_password = st.text_input("New password", type="password")
        confirm_password = st.text_input("Confirm new password", type="password")
        submitted_pass = st.form_submit_button("Change password")

        if submitted_pass:
            if not old_password or not new_password or not confirm_password:
                st.warning("All password fields are required.")
            elif new_password != confirm_password:
                st.warning("New passwords do not match.")
            elif len(new_password) < 6:
                st.warning("New password must be at least 6 characters.")
            else:
                fetch_change_password(old_password, new_password)
                st.success("Password changed successfully!")

    st.markdown('</div>', unsafe_allow_html=True)

if st.button("Logout", key="logout", help="Log out of your account"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("pages/authorization.py")

