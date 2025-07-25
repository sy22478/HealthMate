import streamlit as st

def quick_action_buttons():
    actions = [
        {"label": "Start New Chat", "icon": "💬"},
        {"label": "Log Symptoms", "icon": "📝"},
        {"label": "Add Medication", "icon": "💊"},
        {"label": "Schedule Appointment", "icon": "📅"},
        {"label": "View Reports", "icon": "📄"},
    ]
    cols = st.columns(len(actions))
    for i, action in enumerate(actions):
        with cols[i]:
            if st.button(f"{action['icon']} {action['label']}"):
                with st.spinner(f"{action['label']}..."):
                    st.success(f"(Demo) {action['label']} triggered!") 