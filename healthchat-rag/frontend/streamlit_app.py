import streamlit as st
import requests
import json
from datetime import datetime
import sys
import os

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

# Import authentication and session management
from utils.auth_manager import auth_manager
from utils.session_manager import initialize_session_manager

# App configuration
st.set_page_config(
    page_title="HealthMate - AI Health Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session manager
session_manager, session_middleware = initialize_session_manager(auth_manager)

# Ensure auth manager initializes session state first
auth_manager._initialize_session_state()

# Initialize dashboard-specific session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'quick_action' not in st.session_state:
    st.session_state.quick_action = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Chat'
if 'show_logout_confirm' not in st.session_state:
    st.session_state.show_logout_confirm = False
if 'emergency_active' not in st.session_state:
    st.session_state.emergency_active = False
if 'emergency_message' not in st.session_state:
    st.session_state.emergency_message = None
if 'emergency_recommendations' not in st.session_state:
    st.session_state.emergency_recommendations = None

def send_message(message: str):
    """Send message to chat API with authentication"""
    if not auth_manager.is_authenticated():
        return {"response": "Error: Not authenticated"}
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.post(
        "http://localhost:8003/chat/message",
        json={"message": message},
        headers=headers,
        timeout=30
    )
    if response.status_code == 200:
        try:
            return response.json()
        except Exception:
            return {"response": "Error: Could not process message"}
    elif response.status_code == 401:
        # Token expired, try to refresh
        if auth_manager.refresh_session():
            # Retry with new token
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            response = requests.post(
                "http://localhost:8003/chat/message",
                json={"message": message},
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()
        
        return {"response": "Error: Authentication failed"}
    return {"response": "Error: Could not process message"}

def send_feedback(conversation_id: int, feedback: str):
    """Send feedback with authentication"""
    if not auth_manager.is_authenticated():
        return False
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    data = {"conversation_id": conversation_id, "feedback": feedback}
    response = requests.post(
        "http://localhost:8003/chat/feedback",
        json=data,
        headers=headers,
        timeout=10
    )
    return response.status_code == 200

def fetch_history():
    """Fetch conversation history with authentication"""
    if not auth_manager.is_authenticated():
        return []
    
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    response = requests.get(
        "http://localhost:8003/chat/history",
        headers=headers,
        timeout=10
    )
    if response.status_code == 200:
        return response.json()
    return []

def logout():
    """Logout user using authentication manager"""
    auth_manager.logout()
    st.rerun()

# Custom CSS for enhanced UI/UX
st.markdown("""
<style>
    /* Enhanced styling for better accessibility and UX */
    .main-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .nav-button {
        background-color: #f0f2f6;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        transition: all 0.3s ease;
    }
    
    .nav-button:hover {
        background-color: #e0e0e0;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .current-page {
        background-color: #1f77b4 !important;
        color: white !important;
        border-color: #1f77b4 !important;
    }
    
    .breadcrumb {
        background-color: #f8f9fa;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
    
    .user-profile {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    .quick-action {
        background-color: #e8f4fd;
        border: 1px solid #b3d9ff;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.25rem 0;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .quick-action:hover {
        background-color: #b3d9ff;
        transform: scale(1.02);
    }
    
    .emergency-warning {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #f39c12;
    }
    
    /* Accessibility improvements */
    .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }
    
    /* Focus indicators for keyboard navigation */
    button:focus, input:focus, select:focus, textarea:focus {
        outline: 2px solid #1f77b4;
        outline-offset: 2px;
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .nav-button {
            border: 2px solid #000;
        }
        
        .current-page {
            border: 2px solid #000;
        }
    }
    
    /* Reduced motion support */
    @media (prefers-reduced-motion: reduce) {
        .nav-button, .quick-action {
            transition: none;
        }
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Process session management middleware
    session_middleware.process_request()
    
    # Main HealthMate chatbot interface - conditional based on authentication
    if auth_manager.is_authenticated():
        st.markdown("""
        <div class="main-header">
            <h1>🏥 HealthMate - AI Health Assistant</h1>
            <p>Your AI-powered health companion</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Welcome message with user info
        user_info = auth_manager.get_user_info()
        if user_info.get('email'):
            user_display_name = user_info.get('profile', {}).get('full_name', user_info['email'].split('@')[0])
            st.markdown(f"""
            <div class="user-profile">
                <h3>Welcome back, {user_display_name}! 👋</h3>
                <p>Your AI-powered health assistant is ready to help you with health questions and guidance.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="user-profile">
                <h3>Welcome to HealthMate! 👋</h3>
                <p>Your AI-powered health assistant is ready to help you with health questions and guidance.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Conditional sidebar - only show after authentication
    if auth_manager.is_authenticated():
        with st.sidebar:
            # HealthMate branding
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="margin: 0; color: #1f77b4;">🏥 HealthMate</h2>
                <p style="margin: 0; font-size: 0.9rem; color: #666;">AI Health Assistant</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # User profile section
            st.markdown("### 👤 User Profile")
            user_info = auth_manager.get_user_info()
            if user_info.get('email'):
                user_display_name = user_info.get('profile', {}).get('full_name', user_info['email'].split('@')[0])
                st.markdown(f"**{user_display_name}**")
                st.caption(f"📧 {user_info['email']}")
                
                # Show user status
                if st.session_state.get('last_login'):
                    st.caption(f"🕒 Last active: {st.session_state.last_login}")
            
            st.markdown("---")
            
            # Simple navigation for chatbot
            st.markdown("### 🧭 Navigation")
            
            # Only show essential navigation for chatbot
            nav_options = {
                "Chat": {"icon": "💬", "desc": "Chat with AI Health Assistant"},
                "Chat History": {"icon": "📝", "desc": "View conversation history"},
                "Settings": {"icon": "⚙️", "desc": "Account & app preferences"}
            }
            
            # Create navigation buttons
            selected_page = st.session_state.get('current_page', 'Chat')
            
            for nav_name, nav_info in nav_options.items():
                # Create a button-like appearance
                if st.button(
                    f"{nav_info['icon']} {nav_name}",
                    key=f"nav_{nav_name}",
                    use_container_width=True,
                    help=nav_info['desc']
                ):
                    selected_page = nav_name
                    st.session_state.current_page = nav_name
                    st.rerun()
            
            # Highlight current page
            if selected_page in nav_options:
                st.markdown(f"**📍 Current: {nav_options[selected_page]['icon']} {selected_page}**")
            
            st.markdown("---")
            
            # Display session information and controls
            session_middleware.display_session_ui()
            
            # Account section
            st.markdown("### 🔐 Account")
            
            # Logout button with confirmation
            if st.button("🚪 Logout", key="logout_btn", use_container_width=True, type="secondary"):
                st.session_state.show_logout_confirm = True
            
            if st.session_state.get('show_logout_confirm'):
                st.warning("Are you sure you want to logout?")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Yes, Logout", key="confirm_logout"):
                        logout()
                with col2:
                    if st.button("❌ Cancel", key="cancel_logout"):
                        st.session_state.show_logout_confirm = False
                        st.rerun()
    else:
        # Minimal sidebar for unauthenticated users
        with st.sidebar:
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h2 style="margin: 0; color: #1f77b4;">🏥 HealthMate</h2>
                <p style="margin: 0; font-size: 0.9rem; color: #666;">AI Health Assistant</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            st.markdown("### 🔐 Authentication")
            st.markdown("Please log in to access the HealthMate AI Health Assistant.")
            
            st.markdown("---")
            
            # Simple authentication navigation
            if st.button("🔑 Login / Register", key="auth_nav", use_container_width=True):
                st.switch_page("pages/unified_auth.py")
    
    # Main content area - conditional based on authentication
    if auth_manager.is_authenticated():
        # Show chatbot interface for authenticated users
        selected_page = st.session_state.get('current_page', 'Chat')
        
        # Add breadcrumb navigation with enhanced styling
        st.markdown(f"""
        <div class="breadcrumb">
            <span style="color: #666;">🏥 HealthMate</span> 
            <span style="color: #999;">→</span> 
            <span style="color: #1f77b4; font-weight: bold;">{selected_page}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Simplified page routing - only chatbot features
        if selected_page == "Chat":
            show_chat_interface()
        elif selected_page == "Chat History":
            show_chat_history()
        elif selected_page == "Settings":
            show_settings()
        else:
            # Fallback to chat if unknown page
            st.session_state.current_page = "Chat"
            show_chat_interface()
    else:
        # Show authentication interface for unauthenticated users
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <h1>🏥 HealthMate - AI Health Assistant</h1>
            <p style="font-size: 1.2rem; color: #666; margin-bottom: 2rem;">
                Your AI-powered health companion
            </p>
            <div style="max-width: 400px; margin: 0 auto;">
                <p style="margin-bottom: 2rem;">
                    Welcome to HealthMate! Please log in or create an account to access your AI health assistant.
                </p>
                <div style="display: flex; gap: 1rem; justify-content: center;">
                    <button onclick="window.location.href='pages/unified_auth.py'" style="padding: 0.75rem 1.5rem; background-color: #1f77b4; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        🔑 Login / Register
                    </button>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_chat_interface():
    """Display the main chat interface"""
    st.subheader("💬 Chat with Your Health Assistant")
    st.markdown("Ask me anything about your health, symptoms, medications, or general wellness questions.")
    
    # Quick action buttons for common health queries
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🏥 Health Check", use_container_width=True):
            st.session_state.quick_action = "health_check"
    with col2:
        if st.button("💊 Medication Info", use_container_width=True):
            st.session_state.quick_action = "medication_info"
    with col3:
        if st.button("🥗 Nutrition Advice", use_container_width=True):
            st.session_state.quick_action = "nutrition_advice"
    
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
            st.rerun()
        st.stop()
    
    # Always fetch fresh chat history to ensure we have the latest data
    st.session_state.chat_history = fetch_history()
    
    # Display chat history
    for idx, message in enumerate(st.session_state.chat_history):
        with st.chat_message(message["role"]):
            st.write(message["content"])
            # Feedback for assistant messages with valid id
            if message["role"] == "assistant" and "id" in message:
                feedback = message.get("feedback")
                col1, col2 = st.columns([1,1])
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
                msg_id = response.get("id")
            else:
                content = response
                msg_id = None
            assistant_msg = {"role": "assistant", "content": content}
            if msg_id is not None:
                assistant_msg["id"] = msg_id
            st.session_state.chat_history.append(assistant_msg)
            st.rerun()

def show_health_metrics():
    """Display health metrics page"""
    st.subheader("📊 Health Metrics")
    st.markdown("Track and visualize your health data and trends.")
    
    # Health metrics tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Vital Signs", "⚖️ Weight & BMI", "💊 Medications", "📋 Symptoms"])
    
    with tab1:
        st.markdown("### Vital Signs Tracking")
        
        # Blood pressure
        col1, col2 = st.columns(2)
        with col1:
            systolic = st.number_input("Systolic (mmHg)", min_value=70, max_value=200, value=120, help="Top number in blood pressure reading")
        with col2:
            diastolic = st.number_input("Diastolic (mmHg)", min_value=40, max_value=130, value=80, help="Bottom number in blood pressure reading")
        
        # Blood pressure interpretation
        if systolic and diastolic:
            if systolic < 120 and diastolic < 80:
                st.success("✅ Normal blood pressure")
            elif systolic < 130 and diastolic < 80:
                st.warning("⚠️ Elevated blood pressure")
            elif systolic >= 130 or diastolic >= 80:
                st.error("🚨 High blood pressure - Consider consulting a doctor")
        
        # Heart rate
        heart_rate = st.number_input("Heart Rate (bpm)", min_value=40, max_value=200, value=72, help="Resting heart rate")
        if heart_rate:
            if 60 <= heart_rate <= 100:
                st.success(f"✅ Normal heart rate: {heart_rate} bpm")
            elif heart_rate < 60:
                st.info(f"ℹ️ Low heart rate: {heart_rate} bpm (may be normal for athletes)")
            else:
                st.warning(f"⚠️ Elevated heart rate: {heart_rate} bpm")
        
        # Temperature
        temperature = st.number_input("Temperature (°F)", min_value=95.0, max_value=105.0, value=98.6, step=0.1)
        if temperature:
            if 97.0 <= temperature <= 99.0:
                st.success(f"✅ Normal temperature: {temperature}°F")
            elif temperature > 99.0:
                st.warning(f"⚠️ Elevated temperature: {temperature}°F")
            else:
                st.info(f"ℹ️ Low temperature: {temperature}°F")
    
    with tab2:
        st.markdown("### Weight & BMI Calculator")
        
        col1, col2 = st.columns(2)
        with col1:
            weight_lbs = st.number_input("Weight (lbs)", min_value=50.0, max_value=500.0, value=150.0, step=0.1)
        with col2:
            height_inches = st.number_input("Height (inches)", min_value=48, max_value=84, value=67, help="Total height in inches")
        
        if weight_lbs and height_inches:
            # Calculate BMI
            height_meters = height_inches * 0.0254
            weight_kg = weight_lbs * 0.453592
            bmi = weight_kg / (height_meters ** 2)
            
            st.metric("BMI", f"{bmi:.1f}")
            
            # BMI interpretation
            if bmi < 18.5:
                st.info("📊 Underweight")
            elif 18.5 <= bmi < 25:
                st.success("📊 Normal weight")
            elif 25 <= bmi < 30:
                st.warning("📊 Overweight")
            else:
                st.error("📊 Obese")
            
            # Weight tracking
            st.markdown("### Weight History")
            weight_history = st.session_state.get('weight_history', [])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button("📝 Add Today's Weight"):
                    from datetime import datetime
                    weight_history.append({
                        'date': datetime.now().strftime('%Y-%m-%d'),
                        'weight': weight_lbs
                    })
                    st.session_state.weight_history = weight_history
                    st.success("Weight recorded!")
            with col2:
                if st.button("🗑️ Clear History", type="secondary"):
                    st.session_state.weight_history = []
                    st.rerun()
            
            if weight_history:
                st.markdown("**Recent Weight Entries:**")
                for entry in weight_history[-5:]:  # Show last 5 entries
                    st.text(f"{entry['date']}: {entry['weight']} lbs")
    
    with tab3:
        st.markdown("### Medication Tracker")
        
        # Current medications
        st.markdown("#### Current Medications")
        medications = st.session_state.get('medications', [])
        
        # Add new medication
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_med = st.text_input("Medication Name", placeholder="e.g., Aspirin 81mg")
        with col2:
            dosage = st.text_input("Dosage", placeholder="e.g., 1 tablet")
        with col3:
            frequency = st.selectbox("Frequency", ["Daily", "Twice daily", "As needed", "Weekly"])
        
        if st.button("➕ Add Medication"):
            if new_med:
                medications.append({
                    'name': new_med,
                    'dosage': dosage,
                    'frequency': frequency,
                    'added_date': datetime.now().strftime('%Y-%m-%d')
                })
                st.session_state.medications = medications
                st.success("Medication added!")
                st.rerun()
        
        # Display medications
        if medications:
            for i, med in enumerate(medications):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{med['name']}** - {med['dosage']} ({med['frequency']})")
                with col2:
                    if st.button("✅", key=f"taken_{i}", help="Mark as taken"):
                        if 'taken_today' not in med:
                            med['taken_today'] = True
                            st.success("Marked as taken!")
                with col3:
                    if st.button("🗑️", key=f"remove_{i}", help="Remove medication"):
                        medications.pop(i)
                        st.session_state.medications = medications
                        st.rerun()
        else:
            st.info("No medications added yet.")
    
    with tab4:
        st.markdown("### Symptom Tracker")
        
        # Common symptoms
        symptoms = [
            "Headache", "Fever", "Cough", "Fatigue", "Nausea", 
            "Dizziness", "Chest pain", "Shortness of breath", "Joint pain"
        ]
        
        st.markdown("#### Track Today's Symptoms")
        selected_symptoms = st.multiselect("Select symptoms you're experiencing:", symptoms)
        
        if selected_symptoms:
            st.markdown("**Selected Symptoms:**")
            for symptom in selected_symptoms:
                severity = st.slider(f"Severity of {symptom} (1-10)", 1, 10, 5, key=f"severity_{symptom}")
                
                if severity >= 8:
                    st.warning(f"⚠️ {symptom}: High severity ({severity}/10) - Consider seeking medical attention")
                elif severity >= 5:
                    st.info(f"ℹ️ {symptom}: Moderate severity ({severity}/10)")
                else:
                    st.success(f"✅ {symptom}: Mild severity ({severity}/10)")
        
        # Save symptoms
        if st.button("💾 Save Symptom Report"):
            if selected_symptoms:
                symptom_report = {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'symptoms': selected_symptoms
                }
                symptom_history = st.session_state.get('symptom_history', [])
                symptom_history.append(symptom_report)
                st.session_state.symptom_history = symptom_history
                st.success("Symptom report saved!")
            else:
                st.info("No symptoms selected to save.")

def show_health_profile():
    """Display health profile page"""
    st.subheader("👤 Health Profile")
    st.markdown("Manage your personal health information and preferences.")
    
    # Profile tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Personal Info", "🏥 Medical History", "👨‍👩‍👧‍👦 Family History", "🎯 Health Goals"])
    
    with tab1:
        st.markdown("### Personal Information")
        
        # Basic info
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full Name", value=st.session_state.get('full_name', ''), placeholder="Enter your full name")
            age = st.number_input("Age", min_value=0, max_value=120, value=st.session_state.get('age', 25))
            gender = st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"], index=0)
        with col2:
            height_cm = st.number_input("Height (cm)", min_value=100, max_value=250, value=st.session_state.get('height_cm', 170))
            weight_kg = st.number_input("Weight (kg)", min_value=30, max_value=300, value=st.session_state.get('weight_kg', 70))
            blood_type = st.selectbox("Blood Type", ["Unknown", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"], index=0)
        
        # Contact info
        st.markdown("### Contact Information")
        col1, col2 = st.columns(2)
        with col1:
            email = st.text_input("Email", value=st.session_state.get('email', auth_manager.get_user_info().get('email')), disabled=True)
            phone = st.text_input("Phone Number", value=st.session_state.get('phone', ''), placeholder="Enter phone number")
        with col2:
            emergency_contact = st.text_input("Emergency Contact", value=st.session_state.get('emergency_contact', ''), placeholder="Name and phone")
            address = st.text_area("Address", value=st.session_state.get('address', ''), placeholder="Enter your address")
        
        # Save personal info
        if st.button("💾 Save Personal Information"):
            st.session_state.full_name = full_name
            st.session_state.age = age
            st.session_state.gender = gender
            st.session_state.height_cm = height_cm
            st.session_state.weight_kg = weight_kg
            st.session_state.blood_type = blood_type
            st.session_state.phone = phone
            st.session_state.emergency_contact = emergency_contact
            st.session_state.address = address
            st.success("Personal information saved!")
    
    with tab2:
        st.markdown("### Medical History")
        
        # Chronic conditions
        st.markdown("#### Chronic Conditions")
        chronic_conditions = st.session_state.get('chronic_conditions', [])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_condition = st.text_input("Add Condition", placeholder="e.g., Diabetes, Hypertension")
        with col2:
            if st.button("➕ Add"):
                if new_condition and new_condition not in chronic_conditions:
                    chronic_conditions.append(new_condition)
                    st.session_state.chronic_conditions = chronic_conditions
                    st.rerun()
        
        if chronic_conditions:
            for i, condition in enumerate(chronic_conditions):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"• {condition}")
                with col2:
                    if st.button("🗑️", key=f"remove_condition_{i}"):
                        chronic_conditions.pop(i)
                        st.session_state.chronic_conditions = chronic_conditions
                        st.rerun()
        
        # Allergies
        st.markdown("#### Allergies")
        allergies = st.session_state.get('allergies', [])
        
        col1, col2 = st.columns([3, 1])
        with col1:
            new_allergy = st.text_input("Add Allergy", placeholder="e.g., Penicillin, Peanuts")
        with col2:
            if st.button("➕ Add", key="add_allergy"):
                if new_allergy and new_allergy not in allergies:
                    allergies.append(new_allergy)
                    st.session_state.allergies = allergies
                    st.rerun()
        
        if allergies:
            for i, allergy in enumerate(allergies):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"• {allergy}")
                with col2:
                    if st.button("🗑️", key=f"remove_allergy_{i}"):
                        allergies.pop(i)
                        st.session_state.allergies = allergies
                        st.rerun()
        
        # Surgeries
        st.markdown("#### Past Surgeries")
        surgeries = st.session_state.get('surgeries', [])
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            surgery_name = st.text_input("Surgery Name", placeholder="e.g., Appendectomy")
        with col2:
            surgery_year = st.number_input("Year", min_value=1900, max_value=datetime.now().year, value=2020)
        with col3:
            if st.button("➕ Add", key="add_surgery"):
                if surgery_name:
                    surgeries.append({
                        'name': surgery_name,
                        'year': surgery_year
                    })
                    st.session_state.surgeries = surgeries
                    st.rerun()
        
        if surgeries:
            for i, surgery in enumerate(surgeries):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"• {surgery['name']} ({surgery['year']})")
                with col2:
                    if st.button("🗑️", key=f"remove_surgery_{i}"):
                        surgeries.pop(i)
                        st.session_state.surgeries = surgeries
                        st.rerun()
    
    with tab3:
        st.markdown("### Family Medical History")
        
        # Family conditions
        family_conditions = st.session_state.get('family_conditions', {})
        
        conditions = [
            "Heart Disease", "Diabetes", "Cancer", "High Blood Pressure", 
            "Asthma", "Depression", "Alzheimer's", "Stroke"
        ]
        
        st.markdown("#### Family Members with Medical Conditions")
        
        for condition in conditions:
            st.markdown(f"**{condition}**")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.checkbox(f"Father", key=f"father_{condition}"):
                    if 'father' not in family_conditions:
                        family_conditions['father'] = []
                    if condition not in family_conditions['father']:
                        family_conditions['father'].append(condition)
            with col2:
                if st.checkbox(f"Mother", key=f"mother_{condition}"):
                    if 'mother' not in family_conditions:
                        family_conditions['mother'] = []
                    if condition not in family_conditions['mother']:
                        family_conditions['mother'].append(condition)
            with col3:
                if st.checkbox(f"Sibling", key=f"sibling_{condition}"):
                    if 'sibling' not in family_conditions:
                        family_conditions['sibling'] = []
                    if condition not in family_conditions['sibling']:
                        family_conditions['sibling'].append(condition)
            with col4:
                if st.checkbox(f"Other", key=f"other_{condition}"):
                    if 'other' not in family_conditions:
                        family_conditions['other'] = []
                    if condition not in family_conditions['other']:
                        family_conditions['other'].append(condition)
        
        st.session_state.family_conditions = family_conditions
        
        # Display summary
        if family_conditions:
            st.markdown("#### Family History Summary")
            for member, conditions_list in family_conditions.items():
                if conditions_list:
                    st.markdown(f"**{member.title()}:** {', '.join(conditions_list)}")
    
    with tab4:
        st.markdown("### Health Goals")
        
        goals = st.session_state.get('health_goals', [])
        
        # Add new goal
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_goal = st.text_input("New Goal", placeholder="e.g., Lose 10 pounds, Exercise 3 times per week")
        with col2:
            goal_type = st.selectbox("Type", ["Weight", "Exercise", "Nutrition", "Mental Health", "Other"])
        with col3:
            if st.button("➕ Add Goal"):
                if new_goal:
                    goals.append({
                        'description': new_goal,
                        'type': goal_type,
                        'created_date': datetime.now().strftime('%Y-%m-%d'),
                        'completed': False
                    })
                    st.session_state.health_goals = goals
                    st.rerun()
        
        # Display goals
        if goals:
            st.markdown("#### Current Goals")
            for i, goal in enumerate(goals):
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    status = "✅" if goal['completed'] else "⏳"
                    st.markdown(f"{status} **{goal['description']}** ({goal['type']})")
                with col2:
                    if not goal['completed']:
                        if st.button("✅", key=f"complete_{i}", help="Mark as completed"):
                            goal['completed'] = True
                            st.session_state.health_goals = goals
                            st.rerun()
                with col3:
                    if st.button("📝", key=f"edit_{i}", help="Edit goal"):
                        # Simple edit - could be enhanced with a modal
                        st.info("Edit functionality can be enhanced with a modal dialog")
                with col4:
                    if st.button("🗑️", key=f"remove_goal_{i}", help="Remove goal"):
                        goals.pop(i)
                        st.session_state.health_goals = goals
                        st.rerun()
        
        # Goal statistics
        if goals:
            completed_goals = len([g for g in goals if g['completed']])
            total_goals = len(goals)
            completion_rate = (completed_goals / total_goals) * 100 if total_goals > 0 else 0
            
            st.markdown("#### Goal Progress")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Goals", total_goals)
            with col2:
                st.metric("Completed", completed_goals)
            with col3:
                st.metric("Completion Rate", f"{completion_rate:.1f}%")

def show_chat_history():
    """Display chat history page"""
    st.subheader("📝 Chat History")
    st.markdown("View and manage your conversation history with the health assistant.")
    
    # Always fetch fresh chat history to ensure we have the latest data
    st.session_state.chat_history = fetch_history()
    
    if not st.session_state.chat_history:
        st.info("No chat history found. Start a conversation in the Chat section!")
        return
    
    # Chat history controls
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search conversations", placeholder="Search by message content...")
    with col2:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.chat_history = fetch_history()
            st.rerun()
    with col3:
        if st.button("🗑️ Clear History", use_container_width=True, type="secondary"):
            if st.session_state.chat_history:
                st.session_state.chat_history = []
                st.success("Chat history cleared!")
                st.rerun()
    
    st.markdown("---")
    
    # Filter chat history based on search term
    filtered_history = st.session_state.chat_history
    if search_term:
        filtered_history = [
            msg for msg in st.session_state.chat_history 
            if search_term.lower() in msg.get("content", "").lower()
        ]
    
    if not filtered_history:
        st.info("No conversations match your search criteria.")
        return
    
    # Display chat history with timestamps and details
    for idx, message in enumerate(filtered_history):
        # Create a container for each message
        with st.container():
            # Message header with timestamp and role
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                role_icon = "👤" if message["role"] == "user" else "🤖"
                st.markdown(f"**{role_icon} {message['role'].title()}**")
            with col2:
                # Show timestamp if available
                if "timestamp" in message:
                    timestamp = message["timestamp"]
                    if isinstance(timestamp, str):
                        st.caption(f"📅 {timestamp}")
                    else:
                        st.caption(f"📅 {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    st.caption("📅 Recent")
            with col3:
                # Message actions
                if message["role"] == "assistant" and "id" in message:
                    feedback = message.get("feedback")
                    if feedback == "up":
                        st.markdown("👍 ✅")
                    elif feedback == "down":
                        st.markdown("👎 ✅")
                    else:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("👍", key=f"hist_up_{idx}", help="Mark as helpful"):
                                if send_feedback(message["id"], "up"):
                                    st.session_state.chat_history[idx]["feedback"] = "up"
                                    st.rerun()
                        with col_b:
                            if st.button("👎", key=f"hist_down_{idx}", help="Mark as unhelpful"):
                                if send_feedback(message["id"], "down"):
                                    st.session_state.chat_history[idx]["feedback"] = "down"
                                    st.rerun()
            
            # Message content
            with st.chat_message(message["role"]):
                st.write(message["content"])
                
                # Show additional details for assistant messages
                if message["role"] == "assistant":
                    if "context_used" in message and message["context_used"]:
                        with st.expander("📚 Sources Used"):
                            st.markdown(message["context_used"])
                    
                    # Show confidence or other metadata if available
                    if "confidence" in message:
                        confidence = message["confidence"]
                        if confidence > 0.8:
                            st.success(f"Confidence: {confidence:.1%}")
                        elif confidence > 0.6:
                            st.warning(f"Confidence: {confidence:.1%}")
                        else:
                            st.error(f"Confidence: {confidence:.1%}")
        
        # Add separator between messages
        if idx < len(filtered_history) - 1:
            st.markdown("---")
    
    # Summary statistics
    st.markdown("---")
    st.subheader("📊 Conversation Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    total_messages = len(st.session_state.chat_history)
    user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
    assistant_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
    positive_feedback = len([msg for msg in st.session_state.chat_history if msg.get("feedback") == "up"])
    
    with col1:
        st.metric("Total Messages", total_messages)
    with col2:
        st.metric("Your Messages", user_messages)
    with col3:
        st.metric("Assistant Responses", assistant_messages)
    with col4:
        st.metric("Helpful Responses", positive_feedback)

def show_reports():
    """Display reports page"""
    st.subheader("📋 Health Reports")
    st.markdown("Generate comprehensive health reports and insights.")
    
    # Report types
    report_type = st.selectbox(
        "Select Report Type",
        ["Health Summary", "Chat Analysis", "Medication Report", "Symptom Trends", "Custom Report"]
    )
    
    if report_type == "Health Summary":
        show_health_summary_report()
    elif report_type == "Chat Analysis":
        show_chat_analysis_report()
    elif report_type == "Medication Report":
        show_medication_report()
    elif report_type == "Symptom Trends":
        show_symptom_trends_report()
    elif report_type == "Custom Report":
        show_custom_report()

def show_health_summary_report():
    """Generate health summary report"""
    st.markdown("### 📊 Health Summary Report")
    
    # Report date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now().date())
    with col2:
        end_date = st.date_input("End Date", value=datetime.now().date())
    
    if st.button("📄 Generate Health Summary"):
        with st.spinner("Generating report..."):
            # Collect data from session state
            health_data = {
                'personal_info': {
                    'name': st.session_state.get('full_name', 'Not provided'),
                    'age': st.session_state.get('age', 'Not provided'),
                    'gender': st.session_state.get('gender', 'Not provided'),
                    'blood_type': st.session_state.get('blood_type', 'Unknown')
                },
                'vitals': {
                    'height_cm': st.session_state.get('height_cm', 0),
                    'weight_kg': st.session_state.get('weight_kg', 0),
                    'bmi': calculate_bmi(st.session_state.get('height_cm', 0), st.session_state.get('weight_kg', 0))
                },
                'medical_history': {
                    'chronic_conditions': st.session_state.get('chronic_conditions', []),
                    'allergies': st.session_state.get('allergies', []),
                    'surgeries': st.session_state.get('surgeries', [])
                },
                'current_medications': st.session_state.get('medications', []),
                'health_goals': st.session_state.get('health_goals', [])
            }
            
            # Display report
            st.markdown("---")
            st.markdown("## Health Summary Report")
            st.markdown(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown(f"**Report Period:** {start_date} to {end_date}")
            
            # Personal Information
            st.markdown("### Personal Information")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Name:** {health_data['personal_info']['name']}")
                st.markdown(f"**Age:** {health_data['personal_info']['age']}")
            with col2:
                st.markdown(f"**Gender:** {health_data['personal_info']['gender']}")
                st.markdown(f"**Blood Type:** {health_data['personal_info']['blood_type']}")
            
            # Vital Statistics
            st.markdown("### Vital Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Height", f"{health_data['vitals']['height_cm']} cm")
            with col2:
                st.metric("Weight", f"{health_data['vitals']['weight_kg']} kg")
            with col3:
                bmi = health_data['vitals']['bmi']
                st.metric("BMI", f"{bmi:.1f}")
                if bmi > 0:
                    if bmi < 18.5:
                        st.info("Underweight")
                    elif bmi < 25:
                        st.success("Normal")
                    elif bmi < 30:
                        st.warning("Overweight")
                    else:
                        st.error("Obese")
            
            # Medical History
            st.markdown("### Medical History")
            if health_data['medical_history']['chronic_conditions']:
                st.markdown("**Chronic Conditions:**")
                for condition in health_data['medical_history']['chronic_conditions']:
                    st.markdown(f"• {condition}")
            else:
                st.info("No chronic conditions recorded")
            
            if health_data['medical_history']['allergies']:
                st.markdown("**Allergies:**")
                for allergy in health_data['medical_history']['allergies']:
                    st.markdown(f"• {allergy}")
            else:
                st.info("No allergies recorded")
            
            # Current Medications
            st.markdown("### Current Medications")
            if health_data['current_medications']:
                for med in health_data['current_medications']:
                    st.markdown(f"• **{med['name']}** - {med['dosage']} ({med['frequency']})")
            else:
                st.info("No current medications recorded")
            
            # Health Goals
            st.markdown("### Health Goals")
            if health_data['health_goals']:
                completed_goals = [g for g in health_data['health_goals'] if g['completed']]
                active_goals = [g for g in health_data['health_goals'] if not g['completed']]
                
                if completed_goals:
                    st.markdown("**Completed Goals:**")
                    for goal in completed_goals:
                        st.markdown(f"✅ {goal['description']} ({goal['type']})")
                
                if active_goals:
                    st.markdown("**Active Goals:**")
                    for goal in active_goals:
                        st.markdown(f"⏳ {goal['description']} ({goal['type']})")
            else:
                st.info("No health goals set")
            
            # Export option
            st.markdown("---")
            if st.button("📥 Export Report (PDF)"):
                st.info("PDF export functionality can be implemented with additional libraries")

def show_chat_analysis_report():
    """Generate chat analysis report"""
    st.markdown("### 💬 Chat Analysis Report")
    
    if not st.session_state.chat_history:
        st.info("No chat history available for analysis.")
        return
    
    # Chat statistics
    total_messages = len(st.session_state.chat_history)
    user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
    assistant_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
    positive_feedback = len([msg for msg in st.session_state.chat_history if msg.get("feedback") == "up"])
    
    st.markdown("#### Chat Statistics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Messages", total_messages)
    with col2:
        st.metric("Your Messages", user_messages)
    with col3:
        st.metric("Assistant Responses", assistant_messages)
    with col4:
        st.metric("Helpful Responses", positive_feedback)
    
    # Most common topics (simple analysis)
    st.markdown("#### Common Topics")
    all_text = " ".join([msg.get("content", "") for msg in st.session_state.chat_history])
    common_words = ["health", "pain", "medication", "symptoms", "exercise", "diet", "sleep", "stress"]
    
    topic_counts = {}
    for word in common_words:
        topic_counts[word] = all_text.lower().count(word)
    
    # Display topics with counts
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            st.markdown(f"• **{topic.title()}:** {count} mentions")

def show_medication_report():
    """Generate medication report"""
    st.markdown("### 💊 Medication Report")
    
    medications = st.session_state.get('medications', [])
    
    if not medications:
        st.info("No medications recorded.")
        return
    
    st.markdown("#### Current Medications")
    for i, med in enumerate(medications):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{med['name']}**")
            st.markdown(f"*{med['dosage']} - {med['frequency']}*")
        with col2:
            if med.get('taken_today'):
                st.success("✅ Taken")
            else:
                st.warning("⏳ Pending")
        with col3:
            st.markdown(f"Added: {med.get('added_date', 'Unknown')}")
    
    # Medication adherence
    st.markdown("#### Medication Adherence")
    taken_meds = len([med for med in medications if med.get('taken_today')])
    total_meds = len(medications)
    adherence_rate = (taken_meds / total_meds) * 100 if total_meds > 0 else 0
    
    st.metric("Adherence Rate", f"{adherence_rate:.1f}%")
    
    if adherence_rate >= 80:
        st.success("Excellent medication adherence!")
    elif adherence_rate >= 60:
        st.warning("Good adherence, but room for improvement")
    else:
        st.error("Low adherence - consider setting reminders")

def show_symptom_trends_report():
    """Generate symptom trends report"""
    st.markdown("### 📈 Symptom Trends Report")
    
    symptom_history = st.session_state.get('symptom_history', [])
    
    if not symptom_history:
        st.info("No symptom data available for analysis.")
        return
    
    st.markdown("#### Symptom History")
    for report in symptom_history:
        st.markdown(f"**{report['date']}:** {', '.join(report['symptoms'])}")
    
    # Symptom frequency analysis
    st.markdown("#### Most Common Symptoms")
    all_symptoms = []
    for report in symptom_history:
        all_symptoms.extend(report['symptoms'])
    
    symptom_counts = {}
    for symptom in all_symptoms:
        symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
    
    for symptom, count in sorted(symptom_counts.items(), key=lambda x: x[1], reverse=True):
        st.markdown(f"• **{symptom}:** {count} occurrences")

def show_custom_report():
    """Generate custom report"""
    st.markdown("### 📋 Custom Report")
    
    # Custom report options
    st.markdown("#### Select Data to Include")
    
    include_personal = st.checkbox("Personal Information", value=True)
    include_vitals = st.checkbox("Vital Signs", value=True)
    include_medical = st.checkbox("Medical History", value=True)
    include_medications = st.checkbox("Medications", value=True)
    include_goals = st.checkbox("Health Goals", value=True)
    include_chat = st.checkbox("Chat History", value=False)
    include_symptoms = st.checkbox("Symptom History", value=False)
    
    if st.button("📄 Generate Custom Report"):
        with st.spinner("Generating custom report..."):
            st.markdown("## Custom Health Report")
            st.markdown(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            if include_personal:
                st.markdown("### Personal Information")
                st.markdown(f"**Name:** {st.session_state.get('full_name', 'Not provided')}")
                st.markdown(f"**Age:** {st.session_state.get('age', 'Not provided')}")
                st.markdown(f"**Gender:** {st.session_state.get('gender', 'Not provided')}")
            
            if include_vitals:
                st.markdown("### Vital Signs")
                height = st.session_state.get('height_cm', 0)
                weight = st.session_state.get('weight_kg', 0)
                bmi = calculate_bmi(height, weight)
                st.markdown(f"**Height:** {height} cm")
                st.markdown(f"**Weight:** {weight} kg")
                st.markdown(f"**BMI:** {bmi:.1f}")
            
            if include_medical:
                st.markdown("### Medical History")
                conditions = st.session_state.get('chronic_conditions', [])
                if conditions:
                    st.markdown("**Chronic Conditions:**")
                    for condition in conditions:
                        st.markdown(f"• {condition}")
            
            if include_medications:
                st.markdown("### Medications")
                medications = st.session_state.get('medications', [])
                if medications:
                    for med in medications:
                        st.markdown(f"• **{med['name']}** - {med['dosage']} ({med['frequency']})")
            
            if include_goals:
                st.markdown("### Health Goals")
                goals = st.session_state.get('health_goals', [])
                if goals:
                    for goal in goals:
                        status = "✅" if goal['completed'] else "⏳"
                        st.markdown(f"{status} {goal['description']} ({goal['type']})")
            
            if include_chat:
                st.markdown("### Chat Summary")
                chat_history = st.session_state.get('chat_history', [])
                if chat_history:
                    st.markdown(f"**Total Messages:** {len(chat_history)}")
                    user_msgs = len([msg for msg in chat_history if msg["role"] == "user"])
                    st.markdown(f"**Your Messages:** {user_msgs}")
            
            if include_symptoms:
                st.markdown("### Symptom Summary")
                symptom_history = st.session_state.get('symptom_history', [])
                if symptom_history:
                    st.markdown(f"**Symptom Reports:** {len(symptom_history)}")
                    all_symptoms = []
                    for report in symptom_history:
                        all_symptoms.extend(report['symptoms'])
                    unique_symptoms = list(set(all_symptoms))
                    st.markdown(f"**Unique Symptoms:** {len(unique_symptoms)}")

def calculate_bmi(height_cm, weight_kg):
    """Calculate BMI from height and weight"""
    if height_cm <= 0 or weight_kg <= 0:
        return 0
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)

def show_settings():
    """Display settings page"""
    st.subheader("⚙️ Settings")
    st.markdown("Configure your account preferences and privacy settings.")
    
    # Settings tabs
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Account", "🔔 Notifications", "🔒 Privacy", "🎨 Appearance"])
    
    with tab1:
        st.markdown("### Account Settings")
        
        # Account information
        st.markdown("#### Account Information")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Email", value=auth_manager.get_user_info().get('email'), disabled=True)
            st.text_input("Full Name", value=st.session_state.get('full_name', ''), key="settings_full_name")
        with col2:
            st.number_input("Age", min_value=0, max_value=120, value=st.session_state.get('age', 25), key="settings_age")
            st.selectbox("Gender", ["Prefer not to say", "Male", "Female", "Other"], 
                        index=0 if st.session_state.get('gender') != "Male" and st.session_state.get('gender') != "Female" else 
                        (1 if st.session_state.get('gender') == "Male" else 2), key="settings_gender")
        
        # Password change
        st.markdown("#### Change Password")
        col1, col2 = st.columns(2)
        with col1:
            current_password = st.text_input("Current Password", type="password", placeholder="Enter current password")
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
        with col2:
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")
            if st.button("🔑 Change Password"):
                if new_password and new_password == confirm_password:
                    st.success("Password change request sent! (Backend implementation required)")
                elif new_password != confirm_password:
                    st.error("New passwords do not match!")
                else:
                    st.warning("Please fill all password fields")
        
        # Account actions
        st.markdown("#### Account Actions")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📧 Export Data", use_container_width=True):
                st.info("Data export functionality can be implemented")
        with col2:
            if st.button("🗑️ Delete Account", use_container_width=True, type="secondary"):
                st.error("⚠️ This action cannot be undone!")
                if st.button("Confirm Delete", type="secondary"):
                    st.error("Account deletion requires backend implementation")
    
    with tab2:
        st.markdown("### Notification Settings")
        
        # Email notifications
        st.markdown("#### Email Notifications")
        email_health_reminders = st.checkbox("Health reminders", value=True, help="Receive reminders for medications and appointments")
        email_weekly_reports = st.checkbox("Weekly health reports", value=True, help="Receive weekly health summary reports")
        email_emergency_alerts = st.checkbox("Emergency alerts", value=True, help="Receive alerts for critical health issues")
        email_newsletter = st.checkbox("Health newsletter", value=False, help="Receive monthly health tips and updates")
        
        # In-app notifications
        st.markdown("#### In-App Notifications")
        app_medication_reminders = st.checkbox("Medication reminders", value=True, help="Get reminded to take medications")
        app_goal_reminders = st.checkbox("Goal progress reminders", value=True, help="Get reminded about health goals")
        app_chat_notifications = st.checkbox("Chat notifications", value=True, help="Get notified of new chat responses")
        
        # Notification frequency
        st.markdown("#### Notification Frequency")
        reminder_frequency = st.selectbox(
            "Reminder Frequency",
            ["Daily", "Every 2 days", "Weekly", "Monthly"],
            index=0
        )
        
        # Save notification settings
        if st.button("💾 Save Notification Settings"):
            notification_settings = {
                'email_health_reminders': email_health_reminders,
                'email_weekly_reports': email_weekly_reports,
                'email_emergency_alerts': email_emergency_alerts,
                'email_newsletter': email_newsletter,
                'app_medication_reminders': app_medication_reminders,
                'app_goal_reminders': app_goal_reminders,
                'app_chat_notifications': app_chat_notifications,
                'reminder_frequency': reminder_frequency
            }
            st.session_state.notification_settings = notification_settings
            st.success("Notification settings saved!")
    
    with tab3:
        st.markdown("### Privacy Settings")
        
        # Data sharing
        st.markdown("#### Data Sharing")
        share_health_data = st.checkbox("Share health data for research", value=False, 
                                       help="Anonymously share health data to improve healthcare")
        share_chat_data = st.checkbox("Share chat data for AI improvement", value=True,
                                     help="Share chat conversations to improve AI responses")
        share_analytics = st.checkbox("Share usage analytics", value=True,
                                     help="Share usage data to improve the application")
        
        # Data retention
        st.markdown("#### Data Retention")
        chat_history_retention = st.selectbox(
            "Chat History Retention",
            ["Keep forever", "Keep for 1 year", "Keep for 6 months", "Keep for 1 month"],
            index=0
        )
        
        health_data_retention = st.selectbox(
            "Health Data Retention",
            ["Keep forever", "Keep for 5 years", "Keep for 2 years", "Keep for 1 year"],
            index=0
        )
        
        # Privacy controls
        st.markdown("#### Privacy Controls")
        profile_visibility = st.selectbox(
            "Profile Visibility",
            ["Private", "Friends only", "Public"],
            index=0
        )
        
        allow_data_export = st.checkbox("Allow data export", value=True, help="Allow downloading your health data")
        allow_data_deletion = st.checkbox("Allow data deletion", value=True, help="Allow permanent deletion of your data")
        
        # Save privacy settings
        if st.button("💾 Save Privacy Settings"):
            privacy_settings = {
                'share_health_data': share_health_data,
                'share_chat_data': share_chat_data,
                'share_analytics': share_analytics,
                'chat_history_retention': chat_history_retention,
                'health_data_retention': health_data_retention,
                'profile_visibility': profile_visibility,
                'allow_data_export': allow_data_export,
                'allow_data_deletion': allow_data_deletion
            }
            st.session_state.privacy_settings = privacy_settings
            st.success("Privacy settings saved!")
    
    with tab4:
        st.markdown("### Appearance Settings")
        
        # Theme
        st.markdown("#### Theme")
        theme = st.selectbox(
            "Application Theme",
            ["Light", "Dark", "System Default"],
            index=0
        )
        
        # Font size
        st.markdown("#### Font Size")
        font_size = st.selectbox(
            "Font Size",
            ["Small", "Medium", "Large", "Extra Large"],
            index=1
        )
        
        # Color scheme
        st.markdown("#### Color Scheme")
        color_scheme = st.selectbox(
            "Color Scheme",
            ["Default", "High Contrast", "Color Blind Friendly", "Reduced Motion"],
            index=0
        )
        
        # Layout preferences
        st.markdown("#### Layout Preferences")
        sidebar_position = st.selectbox(
            "Sidebar Position",
            ["Left", "Right"],
            index=0
        )
        
        compact_mode = st.checkbox("Compact mode", value=False, help="Use compact layout for more content")
        show_animations = st.checkbox("Show animations", value=True, help="Enable UI animations")
        
        # Save appearance settings
        if st.button("💾 Save Appearance Settings"):
            appearance_settings = {
                'theme': theme,
                'font_size': font_size,
                'color_scheme': color_scheme,
                'sidebar_position': sidebar_position,
                'compact_mode': compact_mode,
                'show_animations': show_animations
            }
            st.session_state.appearance_settings = appearance_settings
            st.success("Appearance settings saved!")
    
    # Global settings save
    st.markdown("---")
    if st.button("💾 Save All Settings", use_container_width=True):
        st.success("All settings saved successfully!")

if __name__ == "__main__":
    main() 