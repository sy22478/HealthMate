import streamlit as st

st.set_page_config(page_title="Profile | HealthChat RAG", page_icon="👤")

st.title("User Profile")

# Profile picture upload
profile_pic = st.file_uploader("Upload Profile Picture", type=["jpg", "jpeg", "png"])

# Editable profile fields
with st.form("profile_form"):
    full_name = st.text_input("Full Name", value="Jane Doe")
    email = st.text_input("Email", value="jane.doe@email.com")
    age = st.number_input("Age", min_value=0, max_value=120, value=30)
    save = st.form_submit_button("Save Changes")
    cancel = st.form_submit_button("Cancel")
    if save:
        st.success("Profile updated! (Demo)")
    elif cancel:
        st.info("Changes cancelled.")

st.header("Health Profile")

with st.expander("Medical Conditions"):
    medical_conditions = st.text_area("List your medical conditions", placeholder="e.g. Diabetes, Hypertension")
    st.button("Save Medical Conditions")

with st.expander("Medications"):
    medications = st.text_area("Current Medications", placeholder="e.g. Metformin, Lisinopril")
    st.button("Save Medications")

with st.expander("Allergies"):
    allergies = st.text_area("Allergies", placeholder="e.g. Penicillin, Peanuts")
    st.button("Save Allergies")

with st.expander("Emergency Contact"):
    emergency_name = st.text_input("Contact Name", placeholder="Full Name")
    emergency_phone = st.text_input("Contact Phone", placeholder="Phone Number")
    emergency_relation = st.text_input("Relationship", placeholder="e.g. Spouse, Parent")
    st.button("Save Emergency Contact")

st.header("Account Settings")

with st.expander("Change Password"):
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    confirm_new_password = st.text_input("Confirm New Password", type="password")
    st.button("Change Password")

with st.expander("Notification Preferences"):
    email_notifications = st.checkbox("Email Notifications", value=True)
    push_notifications = st.checkbox("Push Notifications", value=False)
    st.button("Save Notification Preferences")

with st.expander("Privacy Settings"):
    data_sharing = st.checkbox("Allow data sharing with research partners", value=False)
    account_visibility = st.selectbox("Account Visibility", ["Private", "Public"])
    st.button("Save Privacy Settings")

with st.expander("Account Deactivation"):
    st.warning("Deactivating your account will disable access to all features. This action can be undone by contacting support.")
    st.button("Deactivate Account") 