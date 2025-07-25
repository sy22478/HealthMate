import streamlit as st

st.set_page_config(page_title="Reset Password | HealthChat RAG", page_icon="🔑")

st.title("Reset Your Password")

with st.form("reset_form"):
    email = st.text_input("Email", placeholder="Enter your registered email")
    submit = st.form_submit_button("Send Reset Link")
    if submit:
        if not email:
            st.error("Please enter your email.")
        else:
            st.success("(Demo) Password reset link sent!") 