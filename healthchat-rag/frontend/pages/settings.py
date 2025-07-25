import streamlit as st

st.set_page_config(page_title="Settings | HealthChat RAG", page_icon="⚙️")
st.title("Settings")

# General Settings
with st.expander("General Preferences", expanded=True):
    st.markdown("### General Preferences")
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("Language", ["English", "Spanish", "French", "German", "Chinese"])
        timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "CST", "MST", "GMT"])
    with col2:
        theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
        measurement_units = st.selectbox("Measurement Units", ["Metric", "Imperial"])
    
    if st.button("Save General Preferences"):
        st.success("(Demo) General preferences saved!")

# Notification Settings
with st.expander("Notification Preferences"):
    st.markdown("### Notification Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        email_notifications = st.checkbox("Email Notifications", value=True)
        push_notifications = st.checkbox("Push Notifications", value=True)
        appointment_reminders = st.checkbox("Appointment Reminders", value=True)
    with col2:
        medication_reminders = st.checkbox("Medication Reminders", value=True)
        health_alerts = st.checkbox("Health Alerts", value=True)
        weekly_reports = st.checkbox("Weekly Health Reports", value=False)
    
    st.markdown("### Reminder Frequency")
    reminder_frequency = st.selectbox("Default Reminder Frequency", [
        "Immediately",
        "15 minutes",
        "1 hour", 
        "3 hours",
        "Daily",
        "Weekly"
    ])
    
    if st.button("Save Notification Preferences"):
        st.success("(Demo) Notification preferences saved!")

# Privacy and Security Settings (placeholder)
with st.expander("Privacy & Security"):
    st.markdown("### Privacy Controls")
    st.write("Privacy controls and data sharing preferences will appear here.")
    st.write("• Data sharing preferences")
    st.write("• Account visibility settings")
    st.write("• Data export/download options")
    
    st.markdown("### Security Settings")
    st.write("Security settings and authentication options will appear here.")
    st.write("• Two-factor authentication")
    st.write("• Active sessions display")
    st.write("• Login history")
    st.write("• Log out all devices")

# Integration Settings (placeholder)
with st.expander("Integrations"):
    st.markdown("### API Connections")
    st.write("Connected apps and third-party integrations will appear here.")
    st.write("• Connected apps display")
    st.write("• App authorization management")
    st.write("• Revoke access buttons")
    
    st.markdown("### Data Import/Export")
    st.write("Data import and export functionality will appear here.")
    st.write("• File upload for health data")
    st.write("• Export format selection")
    st.write("• Backup/restore options") 