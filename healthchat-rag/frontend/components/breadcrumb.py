import streamlit as st
from typing import List

def breadcrumb_trail(trail: List[str], on_click=None):
    """
    Display a breadcrumb trail. Each item except the last is clickable if on_click is provided.
    :param trail: List of breadcrumb names (e.g., ["Dashboard", "Profile", "Edit"])
    :param on_click: Optional callback for click events (not implemented in demo)
    """
    st.markdown("<nav aria-label='breadcrumb' style='margin-bottom: 1rem;'>", unsafe_allow_html=True)
    for i, crumb in enumerate(trail):
        if i < len(trail) - 1:
            st.markdown(f"<span style='color: #2a9d8f; cursor: pointer;'>{crumb}</span> &gt; ", unsafe_allow_html=True)
        else:
            st.markdown(f"<span style='color: #222; font-weight: bold;'>{crumb}</span>", unsafe_allow_html=True)
    st.markdown("</nav>", unsafe_allow_html=True) 