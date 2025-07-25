import streamlit as st

st.set_page_config(page_title="Login | HealthChat RAG", page_icon="🔐")

st.title("Login to HealthChat RAG")

with st.form("login_form"):
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Enter your password")
    remember_me = st.checkbox("Remember Me")
    submit = st.form_submit_button("Login")
    st.markdown("<a href='/forgot-password'>Forgot Password?</a>", unsafe_allow_html=True)
    if submit:
        with st.spinner("Authenticating..."):
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                st.success("(Demo) Login successful!") 