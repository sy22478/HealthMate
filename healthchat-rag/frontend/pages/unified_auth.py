import streamlit as st
import requests
import json
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="HealthMate - Authentication",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .auth-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        background-color: white;
    }
    .form-section {
        margin-bottom: 1.5rem;
    }
    .toggle-link {
        text-align: center;
        margin-top: 1rem;
    }
    .error-message {
        color: #d32f2f;
        background-color: #ffebee;
        padding: 0.5rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    .success-message {
        color: #2e7d32;
        background-color: #e8f5e8;
        padding: 0.5rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
    .password-strength {
        margin-top: 0.5rem;
        font-size: 0.8rem;
    }
    .strength-weak { color: #d32f2f; }
    .strength-medium { color: #f57c00; }
    .strength-strong { color: #2e7d32; }
</style>
""", unsafe_allow_html=True)

# Session state initialization
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'  # 'login', 'register', 'forgot_password'
if 'auth_message' not in st.session_state:
    st.session_state.auth_message = None
if 'auth_message_type' not in st.session_state:
    st.session_state.auth_message_type = None

def check_password_strength(password):
    """Check password strength and return score and feedback"""
    score = 0
    feedback = []
    
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("At least 8 characters")
    
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("At least one uppercase letter")
    
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("At least one lowercase letter")
    
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("At least one number")
    
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    else:
        feedback.append("At least one special character")
    
    if score <= 2:
        return "weak", score, feedback
    elif score <= 3:
        return "medium", score, feedback
    else:
        return "strong", score, feedback

def authenticate_user(email: str, password: str):
    """Authenticate user with backend"""
    try:
        response = requests.post(
            f"{os.environ.get('HEALTHMATE_API_URL', 'http://localhost:8000')}/auth/login",
            json={"email": email, "password": password},
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            st.session_state.authenticated = True
            st.session_state.token = token
            st.session_state.user_email = email
            return True, "Login successful!"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Login failed")
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def register_user(email, password, full_name, age, medical_conditions, medications):
    """Register new user"""
    try:
        response = requests.post(
            f"{os.environ.get('HEALTHMATE_API_URL', 'http://localhost:8000')}/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": full_name,
                "age": age,
                "medical_conditions": medical_conditions,
                "medications": medications
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Registration successful! Please log in."
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Registration failed")
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def request_password_reset(email: str):
    """Request password reset"""
    try:
        response = requests.post(
            f"{os.environ.get('HEALTHMATE_API_URL', 'http://localhost:8000')}/auth/forgot-password",
            json={"email": email},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Password reset link sent to your email"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Password reset request failed")
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def reset_password(token: str, new_password: str):
    """Reset password with token"""
    try:
        response = requests.post(
            f"{os.environ.get('HEALTHMATE_API_URL', 'http://localhost:8000')}/auth/reset-password",
            json={"token": token, "new_password": new_password},
            timeout=10
        )
        
        if response.status_code == 200:
            return True, "Password reset successfully!"
        else:
            error_data = response.json()
            return False, error_data.get("detail", "Password reset failed")
    except requests.exceptions.RequestException as e:
        return False, f"Connection error: {str(e)}"

def main():
    # Header
    st.markdown('<h1 class="main-header">🏥 HealthMate</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">Your AI-powered health assistant</p>', unsafe_allow_html=True)
    
    # Auth container
    with st.container():
        st.markdown('<div class="auth-container">', unsafe_allow_html=True)
        
        # Display message if any
        if st.session_state.auth_message:
            message_class = "success-message" if st.session_state.auth_message_type == "success" else "error-message"
            st.markdown(f'<div class="{message_class}">{st.session_state.auth_message}</div>', unsafe_allow_html=True)
        
        # Mode selection tabs
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Login", use_container_width=True):
                st.session_state.auth_mode = 'login'
                st.session_state.auth_message = None
                st.rerun()
        with col2:
            if st.button("Register", use_container_width=True):
                st.session_state.auth_mode = 'register'
                st.session_state.auth_message = None
                st.rerun()
        with col3:
            if st.button("Forgot Password", use_container_width=True):
                st.session_state.auth_mode = 'forgot_password'
                st.session_state.auth_message = None
                st.rerun()
        
        st.markdown("---")
        
        # Login Form
        if st.session_state.auth_mode == 'login':
            st.subheader("Welcome Back")
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                remember_me = st.checkbox("Remember me")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if not email or not password:
                        st.session_state.auth_message = "Please enter both email and password"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    else:
                        success, message = authenticate_user(email, password)
                        if success:
                            st.session_state.auth_message = message
                            st.session_state.auth_message_type = "success"
                            # Auto-redirect to main dashboard after successful login
                            st.success("Login successful! Redirecting to dashboard...")
                            st.balloons()
                            # Use JavaScript to redirect after a short delay
                            st.markdown("""
                            <script>
                                setTimeout(function() {
                                    window.location.href = '../streamlit_app.py';
                                }, 2000);
                            </script>
                            """, unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.session_state.auth_message = message
                            st.session_state.auth_message_type = "error"
                            st.rerun()
        
        # Register Form
        elif st.session_state.auth_mode == 'register':
            st.subheader("Create Account")
            with st.form("register_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Create a password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter your password")
                full_name = st.text_input("Full Name", placeholder="Enter your full name")
                age = st.number_input("Age", min_value=0, max_value=120, step=1, value=25)
                medical_conditions = st.text_area("Medical Conditions (optional)", placeholder="Any existing medical conditions, separated by commas")
                medications = st.text_area("Current Medications (optional)", placeholder="Current medications, separated by commas")
                terms = st.checkbox("I agree to the Terms and Conditions and Privacy Policy")
                
                # Password strength indicator
                if password:
                    strength, score, feedback = check_password_strength(password)
                    strength_class = f"strength-{strength}"
                    st.markdown(f'<div class="password-strength {strength_class}">Password strength: {strength.title()}</div>', unsafe_allow_html=True)
                
                if st.form_submit_button("Register", use_container_width=True):
                    if not all([email, password, confirm_password, full_name, age, terms]):
                        st.session_state.auth_message = "Please fill all required fields and accept the terms"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    elif password != confirm_password:
                        st.session_state.auth_message = "Passwords do not match"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    elif strength == "weak":
                        st.session_state.auth_message = "Please choose a stronger password"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    else:
                        success, message = register_user(email, password, full_name, age, medical_conditions, medications)
                        st.session_state.auth_message = message
                        st.session_state.auth_message_type = "success" if success else "error"
                        if success:
                            st.session_state.auth_mode = 'login'
                            st.success("Registration successful! Please log in with your new account.")
                            st.balloons()
                        st.rerun()
        
        # Forgot Password Form
        elif st.session_state.auth_mode == 'forgot_password':
            st.subheader("Reset Password")
            st.markdown("Enter your email address and we'll send you a link to reset your password.")
            
            with st.form("forgot_password_form"):
                email = st.text_input("Email", placeholder="Enter your registered email")
                
                if st.form_submit_button("Send Reset Link", use_container_width=True):
                    if not email:
                        st.session_state.auth_message = "Please enter your email address"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    else:
                        success, message = request_password_reset(email)
                        st.session_state.auth_message = message
                        st.session_state.auth_message_type = "success" if success else "error"
                        st.rerun()
            
            # Reset password with token (if provided)
            st.markdown("---")
            st.subheader("Reset with Token")
            st.markdown("If you have a reset token, you can use it here.")
            
            with st.form("reset_password_form"):
                token = st.text_input("Reset Token", placeholder="Enter your reset token")
                new_password = st.text_input("New Password", type="password", placeholder="Enter new password")
                confirm_new_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password")
                
                if st.form_submit_button("Reset Password", use_container_width=True):
                    if not all([token, new_password, confirm_new_password]):
                        st.session_state.auth_message = "Please fill all fields"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    elif new_password != confirm_new_password:
                        st.session_state.auth_message = "Passwords do not match"
                        st.session_state.auth_message_type = "error"
                        st.rerun()
                    else:
                        success, message = reset_password(token, new_password)
                        st.session_state.auth_message = message
                        st.session_state.auth_message_type = "success" if success else "error"
                        if success:
                            st.session_state.auth_mode = 'login'
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown('<p style="text-align: center; color: #666; font-size: 0.9rem;">© 2024 HealthMate. All rights reserved.</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main() 