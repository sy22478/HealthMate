import streamlit as st
import random

def health_insights_widget():
    tips = [
        "Stay hydrated by drinking at least 8 cups of water a day.",
        "Regular exercise can improve your mood and health.",
        "Get at least 7-8 hours of sleep each night.",
        "Eat a balanced diet rich in fruits and vegetables.",
        "Take breaks from screens to reduce eye strain."
    ]
    recommendations = [
        "Based on your recent activity, consider scheduling a check-up.",
        "Your blood pressure readings are improving. Keep it up!",
        "You haven't logged your mood in a while. Try it today.",
        "Remember to take your medications on time.",
        "Explore our new health reports for deeper insights."
    ]
    st.markdown("""
    <div class='card' style='background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); padding: 1.5rem; margin-bottom: 1rem;'>
        <div style='font-size: 1.3rem; font-weight: bold; margin-bottom: 0.5rem;'>Health Insights</div>
        <div style='margin-bottom: 0.7rem;'>💡 <i>{tip}</i></div>
        <div style='margin-bottom: 0.7rem;'>🔎 <b>Personalized Recommendation:</b> {rec}</div>
        <a href='#' style='color: #2a9d8f; text-decoration: underline;'>Learn More</a>
    </div>
    """.format(tip=random.choice(tips), rec=random.choice(recommendations)), unsafe_allow_html=True)

def health_insights_dashboard():
    st.markdown("### AI-Generated Health Insights")
    
    # Insight Categories
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔍 Trend Analysis**")
        insights = [
            "Your blood pressure has decreased by 8% over the last month",
            "Weight loss trend is consistent with your goals",
            "Heart rate variability shows good cardiovascular health",
            "Mood patterns indicate stress during weekdays"
        ]
        for insight in insights:
            st.write(f"• {insight}")
    
    with col2:
        st.markdown("**🎯 Recommendations**")
        recommendations = [
            "Continue current exercise routine - it's working well",
            "Consider stress management techniques for weekdays",
            "Monitor blood pressure weekly instead of daily",
            "Increase water intake to support weight loss"
        ]
        for rec in recommendations:
            st.write(f"• {rec}")
    
    # Risk Factor Indicators
    st.markdown("**⚠️ Risk Factor Analysis**")
    risk_factors = [
        {"factor": "Elevated Blood Pressure", "level": "Medium", "trend": "Improving"},
        {"factor": "Sedentary Lifestyle", "level": "Low", "trend": "Stable"},
        {"factor": "Stress Levels", "level": "Medium", "trend": "Worsening"}
    ]
    
    for risk in risk_factors:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{risk['factor']}**")
        with col2:
            if risk['level'] == 'High':
                st.write(f"🔴 {risk['level']}")
            elif risk['level'] == 'Medium':
                st.write(f"🟡 {risk['level']}")
            else:
                st.write(f"🟢 {risk['level']}")
        with col3:
            if risk['trend'] == 'Improving':
                st.write(f"📈 {risk['trend']}")
            elif risk['trend'] == 'Worsening':
                st.write(f"📉 {risk['trend']}")
            else:
                st.write(f"➡️ {risk['trend']}")
    
    # Improvement Suggestions
    st.markdown("**💡 Improvement Suggestions**")
    suggestions = [
        "Try meditation apps for stress management",
        "Consider a standing desk for work",
        "Join a local walking group",
        "Schedule regular check-ups with your doctor"
    ]
    
    for i, suggestion in enumerate(suggestions, 1):
        st.write(f"{i}. {suggestion}")
    
    # Comparative Analysis
    st.markdown("**📊 Comparative Analysis**")
    st.write("Your health metrics compared to similar age groups:")
    
    metrics_comparison = [
        {"metric": "Blood Pressure", "your_value": "135/85", "avg_value": "128/82", "status": "Above Average"},
        {"metric": "BMI", "your_value": "24.2", "avg_value": "26.1", "status": "Below Average"},
        {"metric": "Daily Steps", "your_value": "8,000", "avg_value": "6,500", "status": "Above Average"}
    ]
    
    for comp in metrics_comparison:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.write(f"**{comp['metric']}**")
        with col2:
            st.write(f"Your: {comp['your_value']}")
        with col3:
            st.write(f"Avg: {comp['avg_value']}")
        with col4:
            if comp['status'] == 'Above Average':
                st.write(f"🟢 {comp['status']}")
            else:
                st.write(f"🔴 {comp['status']}") 