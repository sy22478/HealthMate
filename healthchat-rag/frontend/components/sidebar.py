import streamlit as st
from streamlit_option_menu import option_menu

def dashboard_sidebar():
    with st.sidebar:
        selected = option_menu(
            menu_title=None,
            options=[
                "Dashboard",
                "Health Profile",
                "Chat History",
                "Health Metrics",
                "Reports",
                "Settings"
            ],
            icons=[
                "house",
                "person",
                "chat-dots",
                "activity",
                "file-earmark-text",
                "gear"
            ],
            menu_icon="cast",
            default_index=0,
            orientation="vertical"
        )
        # Collapse/expand functionality placeholder
        st.button("Collapse Sidebar")
    return selected 