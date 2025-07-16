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
        # Fetch chat history after login
        st.session_state.chat_history = fetch_history()
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
        try:
            return response.json()
        except Exception:
            return {"response": "Error: Could not process message"}
    return {"response": "Error: Could not process message"}

def send_feedback(conversation_id: int, feedback: str):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    data = {"conversation_id": conversation_id, "feedback": feedback}
    response = requests.post(
        "http://localhost:8000/chat/feedback",
        json=data,
        headers=headers
    )
    return response.status_code == 200

# Fetch conversation history from backend
def fetch_history():
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get("http://localhost:8000/chat/history", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

# Main UI
if 'emergency_active' not in st.session_state:
    st.session_state.emergency_active = False
if 'emergency_message' not in st.session_state:
    st.session_state.emergency_message = None
if 'emergency_recommendations' not in st.session_state:
    st.session_state.emergency_recommendations = None

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
                        st.session_state.chat_history = []  # Clear chat history after registration
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
        # Emergency warning
        if st.session_state.emergency_active:
            st.error(f"🚨 EMERGENCY: {st.session_state.emergency_message}")
            if st.session_state.emergency_recommendations:
                st.markdown("**Recommendations:**")
                for rec in st.session_state.emergency_recommendations:
                    st.markdown(f"- {rec}")
            if st.button("Acknowledge Emergency Warning"):
                st.session_state.emergency_active = False
                st.session_state.emergency_message = None
                st.session_state.emergency_recommendations = None
            st.stop()
        # Display chat history
        for idx, message in enumerate(st.session_state.chat_history):
            with st.chat_message(message["role"]):
                st.write(message["content"])
                # Feedback for assistant messages with valid id
                if message["role"] == "assistant" and "id" in message:
                    feedback = message.get("feedback")
                    col1, col2, _ = st.columns([1,1,8])
                    with col1:
                        up_label = "👍" if feedback != "up" else "**👍** ✅"
                        if st.button(up_label, key=f"up_btn_{idx}"):
                            if feedback != "up" and send_feedback(message["id"], "up"):
                                st.session_state.chat_history[idx]["feedback"] = "up"
                                st.rerun()
                    with col2:
                        down_label = "👎" if feedback != "down" else "**👎** ✅"
                        if st.button(down_label, key=f"down_btn_{idx}"):
                            if feedback != "down" and send_feedback(message["id"], "down"):
                                st.session_state.chat_history[idx]["feedback"] = "down"
                                st.rerun()
        # Chat input
        if prompt := st.chat_input("Ask about your health..."):
            # Add user message
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            # Get AI response
            with st.spinner("Thinking..."):
                response = send_message(prompt)
            # Emergency detection
            if isinstance(response, dict) and response.get("urgency") == "emergency":
                st.session_state.emergency_active = True
                st.session_state.emergency_message = response.get("message", "Emergency detected.")
                st.session_state.emergency_recommendations = response.get("recommendations", [])
                st.session_state.chat_history.append({"role": "assistant", "content": response.get("message", "")})
                st.rerun()
            else:
                # Handle normal response (dict or string)
                if isinstance(response, dict):
                    content = response.get("message", response.get("response", "Error: Could not process message"))
                else:
                    content = response
                st.session_state.chat_history.append({"role": "assistant", "content": content})
                # Always refresh chat history from backend to get ids/feedback
                st.session_state.chat_history = fetch_history()
                st.rerun()

if __name__ == "__main__":
    main() 