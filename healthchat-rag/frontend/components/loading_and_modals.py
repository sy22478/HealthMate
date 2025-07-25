import streamlit as st
import time

# Loading Spinner Component
def loading_spinner(message="Loading..."):
    with st.spinner(message):
        time.sleep(1)

# Skeleton Loading Screen
def skeleton_loading():
    st.markdown("""
    <div style='background: #eee; height: 80px; border-radius: 8px; margin-bottom: 1rem; animation: pulse 1.5s infinite;'>
    </div>
    <style>
    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.5; }
      100% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

# Progress Bar for Long Operations
def progress_bar_demo():
    progress = st.progress(0)
    for i in range(100):
        time.sleep(0.01)
        progress.progress(i + 1)

# Fade-in Animation
def fade_in(content):
    st.markdown(f"""
    <div style='animation: fadeIn 1s;'>{content}</div>
    <style>@keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}</style>
    """, unsafe_allow_html=True)

# Slide Animation for Modals
def slide_modal(content):
    st.markdown(f"""
    <div style='animation: slideIn 0.5s;'>{content}</div>
    <style>@keyframes slideIn {{ from {{ transform: translateY(40px); opacity: 0; }} to {{ transform: translateY(0); opacity: 1; }} }}</style>
    """, unsafe_allow_html=True)

# Hover Effect Example
def hover_card(content):
    st.markdown(f"""
    <div class='hover-card' style='transition: box-shadow 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-radius: 8px; padding: 1rem; margin-bottom: 1rem;'>
      {content}
    </div>
    <style>
    .hover-card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.12); background: #f4f4f4; }}
    </style>
    """, unsafe_allow_html=True)

# Reusable Modal Component
def modal_component(title, body, modal_type="info"):
    st.markdown(f"""
    <div class='modal-bg' style='position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; z-index: 9999;'>
      <div class='modal' style='background: #fff; border-radius: 12px; padding: 2rem; min-width: 320px; max-width: 90vw; box-shadow: 0 8px 32px rgba(0,0,0,0.18);'>
        <div style='font-size: 1.3rem; font-weight: bold; margin-bottom: 1rem;'>{title}</div>
        <div style='margin-bottom: 1.2rem;'>{body}</div>
        <button style='background: #2a9d8f; color: #fff; border: none; border-radius: 6px; padding: 0.5rem 1.2rem; font-size: 1rem; cursor: pointer;'>Close</button>
      </div>
    </div>
    """, unsafe_allow_html=True)

# Modal Types: confirmation, form input, preview, help (placeholders)
def confirmation_modal():
    modal_component("Confirm Action", "Are you sure you want to proceed?", modal_type="confirmation")
def form_input_modal():
    modal_component("Form Input", "Form fields go here.", modal_type="form")
def preview_modal():
    modal_component("Preview", "Preview content goes here.", modal_type="preview")
def help_modal():
    modal_component("Help", "Help and information content.", modal_type="help") 