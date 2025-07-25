import streamlit as st

def main_content_container():
    st.markdown("""
    <div class='dashboard-main' style='overflow-y: auto; min-height: 80vh;'>
        <!-- Main content will be rendered here -->
    </div>
    """, unsafe_allow_html=True)

# Responsive 12-column grid system (CSS-based, for demonstration)
def grid_row(*columns):
    col_count = len(columns)
    col_width = int(12 / col_count) if col_count else 12
    st.markdown("<div class='row' style='display: flex; gap: 1rem;'>", unsafe_allow_html=True)
    for col in columns:
        st.markdown(f"<div class='col' style='flex: 1 1 {col_width}%; padding: 0.5rem;'>" + col + "</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Loading state for page transitions
def show_loading():
    with st.spinner("Loading page..."):
        st.write("") 