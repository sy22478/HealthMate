import streamlit as st
from datetime import datetime, timedelta

def activity_feed():
    activities = [
        {"type": "chat", "icon": "💬", "desc": "Chatted with AI assistant", "time": datetime.now() - timedelta(minutes=5)},
        {"type": "metric", "icon": "📈", "desc": "Logged blood pressure", "time": datetime.now() - timedelta(hours=1)},
        {"type": "medication", "icon": "💊", "desc": "Medication reminder: Metformin", "time": datetime.now() - timedelta(hours=2)},
        {"type": "appointment", "icon": "📅", "desc": "Upcoming appointment: Dr. Smith", "time": datetime.now() - timedelta(days=1)},
    ]
    st.markdown("<div style='margin-bottom: 1rem;'><b>Recent Activity</b></div>", unsafe_allow_html=True)
    for act in activities:
        with st.expander(f"{act['icon']} {act['desc']} ({act['time'].strftime('%Y-%m-%d %H:%M')})"):
            st.write(f"Details for: {act['desc']}")
            st.write("(More info coming soon)")
    st.button("Load More") 