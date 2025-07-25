import streamlit as st

st.set_page_config(page_title="Register | HealthChat RAG", page_icon="📝")

st.title("Create Your HealthChat RAG Account")

with st.form("register_form"):
    email = st.text_input("Email", placeholder="Enter your email")
    password = st.text_input("Password", type="password", placeholder="Create a password")
    confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
    full_name = st.text_input("Full Name", placeholder="Enter your full name")
    age = st.number_input("Age", min_value=0, max_value=120, step=1)
    terms = st.checkbox("I agree to the Terms and Conditions")
    # Password strength indicator placeholder
    st.progress(0)  # Placeholder for password strength
    submit = st.form_submit_button("Register")
    if submit:
        if not (email and password and confirm_password and full_name and age and terms):
            st.error("Please fill all fields and accept the terms.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            st.success("(Demo) Registration successful!") 