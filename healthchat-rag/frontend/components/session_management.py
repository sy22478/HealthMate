import streamlit as st
import time

# Session Timeout Warning Component

def session_timeout_warning(timeout_seconds=300):
    if 'session_timer' not in st.session_state:
        st.session_state.session_timer = timeout_seconds
    if 'show_timeout_warning' not in st.session_state:
        st.session_state.show_timeout_warning = False

    if st.session_state.session_timer <= 60:
        st.session_state.show_timeout_warning = True

    if st.session_state.show_timeout_warning:
        with st.sidebar:
            st.warning(f"Your session will expire in {st.session_state.session_timer} seconds.")
            if st.button("Extend Session"):
                st.session_state.session_timer = timeout_seconds
                st.session_state.show_timeout_warning = False

    # Simulate countdown (for demo only)
    if st.session_state.session_timer > 0:
        st.session_state.session_timer -= 1
        time.sleep(1)
    else:
        st.session_state.authenticated = False
        st.session_state.show_timeout_warning = False
        st.sidebar.error("Session expired. You have been logged out.")

# Logout Confirmation Modal

def logout_confirmation():
    if st.button("Logout"):
        st.session_state.show_logout_modal = True
    if st.session_state.get('show_logout_modal', False):
        st.modal("Confirm Logout")
        st.warning("You have unsaved changes. Are you sure you want to logout?")
        if st.button("Confirm Logout"):
            st.session_state.authenticated = False
            st.session_state.show_logout_modal = False
            st.success("Logged out successfully.")
        if st.button("Cancel"):
            st.session_state.show_logout_modal = False 