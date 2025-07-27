import streamlit as st
from datetime import date
from components.metrics_visualization import metrics_visualization
from components.health_goals import health_goals
from components.metrics_summary import metrics_summary_cards

st.set_page_config(page_title="Health Metrics | HealthChat RAG", page_icon="📊")
st.title("Health Metrics")

# Metrics Input Section
with st.expander("Log New Metrics", expanded=True):
    st.markdown("### Vital Signs")
    col1, col2, col3 = st.columns(3)
    with col1:
        systolic = st.number_input("Systolic BP", min_value=70, max_value=200, value=120)
        diastolic = st.number_input("Diastolic BP", min_value=40, max_value=130, value=80)
    with col2:
        heart_rate = st.number_input("Heart Rate (bpm)", min_value=40, max_value=200, value=72)
        temperature = st.number_input("Temperature (°F)", min_value=95.0, max_value=105.0, value=98.6, step=0.1)
    with col3:
        weight = st.number_input("Weight (lbs)", min_value=50.0, max_value=500.0, value=150.0, step=0.5)
        height = st.number_input("Height (inches)", min_value=36, max_value=84, value=68)
    
    st.markdown("### Mood & Energy")
    col1, col2 = st.columns(2)
    with col1:
        mood = st.slider("Mood (1-10)", 1, 10, 7)
        st.write(f"Current mood: {'😊' if mood > 6 else '😐' if mood > 4 else '😞'}")
    with col2:
        energy = st.slider("Energy Level (1-10)", 1, 10, 6)
        st.write(f"Energy level: {'⚡' * energy}")
    
    st.markdown("### Custom Metrics")
    custom_metric = st.text_input("Custom Metric Name", placeholder="e.g., Blood Sugar, Steps")
    custom_value = st.text_input("Value", placeholder="e.g., 120, 8000")
    
    if st.button("Save Metrics"):
        st.success("(Demo) Metrics saved successfully!")

# Quick Log Buttons
st.markdown("### Quick Log")
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📊 Log Daily Vitals"):
        st.info("(Demo) Quick vitals logging initiated")
with col2:
    if st.button("🤒 Record Symptoms"):
        st.info("(Demo) Symptom recording started")
with col3:
    if st.button("😊 Track Mood"):
        st.info("(Demo) Mood tracking opened")
with col4:
    if st.button("🏃 Log Exercise"):
        st.info("(Demo) Exercise logging started")

# Metrics Visualization
st.markdown("---")
metrics_visualization()

# Health Goals Section
st.markdown("---")
health_goals()

# Metrics Summary Cards
st.markdown("---")
metrics_summary_cards() 