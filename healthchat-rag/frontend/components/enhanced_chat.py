import streamlit as st
import requests

API_BASE_URL = "http://localhost:8000"

class SimpleChatInterface:
    def __init__(self, api_base_url: str = API_BASE_URL):
        self.api_base_url = api_base_url
        self.session = requests.Session()
    
    def setup_page(self):
        st.set_page_config(
            page_title="HealthMate - Medical Chat",
            page_icon="🏥",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        st.title("🏥 HealthMate - Medical Assistant")
        st.markdown("### Ask general medical questions.")
    
    def render_sidebar(self):
        with st.sidebar:
            st.header("Your Profile")
            age = st.number_input("Age", min_value=1, max_value=120, value=30)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
            st.subheader("Medical History")
            medical_conditions = st.text_area(
                "Current Medical Conditions (comma-separated)",
                placeholder="e.g., diabetes, hypertension, asthma"
            )
            st.warning("""
            ⚠️ **Emergency Notice**
            If you're experiencing a medical emergency, please:
            - Call emergency services immediately
            - Go to the nearest emergency room
            - Do not rely on this tool for emergency situations
            """)
            return {
                'age': age,
                'gender': gender,
                'medical_conditions': medical_conditions
            }
    
    def render_chat_interface(self):
        st.header("💬 General Medical Questions")
        user_message = st.text_area(
            "Ask your medical question:",
            placeholder="e.g., What are the symptoms of diabetes? How does blood pressure medication work?",
            height=100
        )
        if st.button("💭 Ask Question", type="primary"):
            if user_message.strip():
                self.perform_chat(user_message)
            else:
                st.error("Please enter a question.")
    
    def perform_chat(self, message: str):
        with st.spinner("Getting response..."):
            try:
                request_data = {
                    "message": message
                }
                response = self.make_api_call("/chat/message", request_data)
                if response:
                    self.display_response(response)
                else:
                    st.error("Failed to get response. Please try again.")
            except Exception as e:
                st.error(f"Error during chat: {str(e)}")
    
    def display_response(self, response: dict):
        st.subheader("💬 Response")
        st.markdown(response.get('response', ''))
    
    def make_api_call(self, endpoint: str, data: dict) -> dict:
        try:
            url = f"{self.api_base_url}{endpoint}"
            headers = {}
            if 'auth_token' in st.session_state:
                headers['Authorization'] = f"Bearer {st.session_state.auth_token}"
            response = self.session.post(url, json=data, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                st.error("Authentication required. Please log in.")
                return None
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error: {str(e)}")
            return None
    
    def run(self):
        self.setup_page()
        profile = self.render_sidebar()
        st.session_state.update(profile)
        self.render_chat_interface()

def main():
    chat_interface = SimpleChatInterface()
    chat_interface.run()

if __name__ == "__main__":
    main() 