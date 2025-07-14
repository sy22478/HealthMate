import streamlit as st
import requests
import json
from datetime import datetime

# App configuration
st.set_page_config(
    page_title="HealthChat RAG",
    page_icon="🏥",
    layout="wide"
)

# Privacy notice
PRIVACY_NOTICE = """
**Privacy Notice**

Your data is used only to provide personalized health insights during your session. We do not share your information with third parties. For your privacy, you may request deletion of your data at any time. This app is for informational purposes only and is not a substitute for professional medical advice.
"""

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'show_register' not in st.session_state:
    st.session_state.show_register = False

def authenticate(email: str, password: str):
    """Authenticate user with backend"""
    response = requests.post(
        "http://localhost:8000/auth/login",
        json={"email": email, "password": password}
    )
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        st.session_state.authenticated = True
        st.session_state.token = token
        return True
    return False

def register_user(email, password, full_name, age, medical_conditions, medications):
    response = requests.post(
        "http://localhost:8000/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "age": age,
            "medical_conditions": medical_conditions,
            "medications": medications
        }
    )
    return response

def send_message(message: str):
    """Send message to chat API"""
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.post(
        "http://localhost:8000/chat/message",
        json={"message": message},
        headers=headers
    )
    
    if response.status_code == 200:
        return response.json()["response"]
    return "Error: Could not process message"

# Main UI
def main():
    st.sidebar.markdown(PRIVACY_NOTICE)
    st.title("🏥 HealthChat RAG")
    st.markdown("Your AI-powered health assistant with personalized medical insights")
    
    if not st.session_state.authenticated:
        # Toggle between login and register
        if st.session_state.show_register:
            with st.form("register_form"):
                st.subheader("Register")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                full_name = st.text_input("Full Name")
                age = st.number_input("Age", min_value=0, max_value=120, step=1)
                medical_conditions = st.text_area("Medical Conditions (comma separated)")
                medications = st.text_area("Medications (comma separated)")
                if st.form_submit_button("Register"):
                    response = register_user(email, password, full_name, age, medical_conditions, medications)
                    if response.status_code == 200:
                        st.success("Registration successful! Please log in.")
                        st.session_state.show_register = False
                    else:
                        try:
                            error = response.json().get("detail", "Registration failed.")
                        except Exception:
                            error = "Registration failed."
                        st.error(error)
            st.button("Back to Login", on_click=lambda: st.session_state.update({"show_register": False}))
        else:
            with st.form("login_form"):
                st.subheader("Login")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login"):
                    if authenticate(email, password):
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            st.button("Register", on_click=lambda: st.session_state.update({"show_register": True}))
    else:
        # Chat interface
        st.subheader("Chat with Your Health Assistant")
        
        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        
        # Chat input
        if prompt := st.chat_input("Ask about your health..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            # Get AI response
            with st.spinner("Thinking..."):
                response = send_message(prompt)
            
            # Add AI response
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            
            st.rerun()

if __name__ == "__main__":
    main() 