import streamlit as st
from datetime import date, timedelta
from components.health_insights import health_insights_dashboard

st.set_page_config(page_title="Reports | HealthChat RAG", page_icon="📄")
st.title("Health Reports")

# Report Generation Section
with st.expander("Generate New Report", expanded=True):
    st.markdown("### Report Type Selection")
    report_type = st.selectbox("Select Report Type", [
        "Health Summary Report",
        "Medication History Report", 
        "Symptom Tracking Report",
        "Custom Report"
    ])
    
    st.markdown("### Report Parameters")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=date.today() - timedelta(days=30))
        end_date = st.date_input("End Date", value=date.today())
    with col2:
        report_format = st.selectbox("Report Format", ["PDF", "CSV", "JSON"])
        email_delivery = st.checkbox("Email Report")
    
    st.markdown("### Metrics to Include")
    metrics_options = [
        "Blood Pressure Readings",
        "Weight Tracking",
        "Heart Rate Data",
        "Mood Tracking",
        "Medication Logs",
        "Exercise Records",
        "Sleep Data",
        "Chat History"
    ]
    selected_metrics = st.multiselect("Select metrics to include", metrics_options, default=metrics_options[:4])
    
    if st.button("Generate Report"):
        with st.spinner("Generating report..."):
            st.success(f"(Demo) {report_type} generated successfully!")
            if email_delivery:
                st.info("Report will be emailed to your registered email address.")

# Generated Reports List
st.markdown("---")
st.markdown("### Generated Reports")
reports = [
    {
        "name": "Health Summary - December 2024",
        "type": "Health Summary Report",
        "date": "2024-12-15",
        "format": "PDF",
        "size": "2.3 MB"
    },
    {
        "name": "Medication History - Q4 2024",
        "type": "Medication History Report", 
        "date": "2024-12-10",
        "format": "PDF",
        "size": "1.8 MB"
    },
    {
        "name": "Symptom Tracking - November 2024",
        "type": "Symptom Tracking Report",
        "date": "2024-11-30",
        "format": "CSV",
        "size": "0.5 MB"
    }
]

for report in reports:
    with st.expander(f"📄 {report['name']}"):
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        with col1:
            st.write(f"**Type:** {report['type']}")
            st.write(f"**Generated:** {report['date']}")
        with col2:
            st.write(f"**Format:** {report['format']}")
        with col3:
            st.write(f"**Size:** {report['size']}")
        with col4:
            if st.button(f"Download {report['name'][:10]}"):
                st.success(f"(Demo) Downloading {report['name']}")
            if st.button(f"View {report['name'][:10]}"):
                st.info(f"(Demo) Preview for {report['name']}")

# Health Insights and Recommendations
st.markdown("---")
health_insights_dashboard() 