import streamlit as st
from datetime import datetime

def dashboard_footer():
    st.markdown("""
    <footer style='margin-top: 2rem; padding: 1rem 0; text-align: center; color: #888; font-size: 0.95rem;'>
        <div>&copy; {year} HealthChat RAG. All rights reserved.</div>
        <div>
            <a href='/terms' style='color: #2a9d8f; text-decoration: none; margin: 0 0.5rem;'>Terms</a> |
            <a href='/privacy' style='color: #2a9d8f; text-decoration: none; margin: 0 0.5rem;'>Privacy Policy</a>
        </div>
        <div>Version 1.0.0 | Last updated: {updated}</div>
    </footer>
    """.format(year=datetime.now().year, updated=datetime.now().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True) 