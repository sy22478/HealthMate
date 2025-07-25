import streamlit as st
from datetime import date, timedelta

def health_goals():
    st.markdown("### Health Goals")
    
    # Display existing goals
    goals = [
        {
            "name": "Weight Loss",
            "current": 150,
            "target": 145,
            "unit": "lbs",
            "progress": 60,
            "deadline": date.today() + timedelta(days=30),
            "achieved": False
        },
        {
            "name": "Blood Pressure Control",
            "current": 135,
            "target": 120,
            "unit": "mmHg",
            "progress": 75,
            "deadline": date.today() + timedelta(days=14),
            "achieved": False
        },
        {
            "name": "Daily Steps",
            "current": 8000,
            "target": 10000,
            "unit": "steps",
            "progress": 80,
            "deadline": date.today() + timedelta(days=7),
            "achieved": False
        }
    ]
    
    for goal in goals:
        with st.expander(f"{goal['name']} - {goal['current']}/{goal['target']} {goal['unit']}"):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.progress(goal['progress'] / 100)
                st.write(f"Progress: {goal['progress']}%")
            with col2:
                days_left = (goal['deadline'] - date.today()).days
                if days_left > 0:
                    st.write(f"⏰ {days_left} days left")
                else:
                    st.write("⏰ Overdue")
            with col3:
                if goal['achieved']:
                    st.write("🏆 Achieved!")
                else:
                    st.write("🎯 In Progress")
    
    # Set New Goal Button
    if st.button("Set New Goal"):
        st.session_state.show_new_goal = True
    
    # New Goal Modal
    if st.session_state.get('show_new_goal', False):
        st.markdown("---")
        st.markdown("**Set New Health Goal**")
        
        goal_type = st.selectbox("Goal Type", [
            "Weight Loss/Gain",
            "Blood Pressure Control",
            "Daily Steps",
            "Exercise Minutes",
            "Water Intake",
            "Sleep Hours",
            "Custom Goal"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            current_value = st.number_input("Current Value", min_value=0.0, value=0.0, step=0.1)
            target_value = st.number_input("Target Value", min_value=0.0, value=0.0, step=0.1)
        with col2:
            unit = st.text_input("Unit", placeholder="lbs, mmHg, steps, etc.")
            deadline = st.date_input("Deadline", value=date.today() + timedelta(days=30))
        
        goal_description = st.text_area("Goal Description", placeholder="Describe your goal and motivation...")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save Goal"):
                st.success("(Demo) New goal created successfully!")
                st.session_state.show_new_goal = False
        with col2:
            if st.button("Cancel"):
                st.session_state.show_new_goal = False 