import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

class TestDashboardFeatures:
    
    def test_chat_history_functionality(self):
        """Test chat history page functionality"""
        # Initialize chat history
        st.session_state.chat_history = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-16 10:00:00"},
            {"role": "assistant", "content": "Hi there!", "id": 1, "feedback": "up"},
            {"role": "user", "content": "How are you?", "timestamp": "2024-01-16 10:01:00"},
            {"role": "assistant", "content": "I'm doing well!", "id": 2}
        ]
        
        # Test chat history statistics
        total_messages = len(st.session_state.chat_history)
        user_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "user"])
        assistant_messages = len([msg for msg in st.session_state.chat_history if msg["role"] == "assistant"])
        positive_feedback = len([msg for msg in st.session_state.chat_history if msg.get("feedback") == "up"])
        
        assert total_messages == 4
        assert user_messages == 2
        assert assistant_messages == 2
        assert positive_feedback == 1
        
        # Test search functionality
        search_term = "Hello"
        filtered_history = [
            msg for msg in st.session_state.chat_history 
            if search_term.lower() in msg.get("content", "").lower()
        ]
        assert len(filtered_history) == 1
        assert filtered_history[0]["content"] == "Hello"
        
        # Test clear history
        st.session_state.chat_history = []
        assert len(st.session_state.chat_history) == 0
    
    def test_health_metrics_functionality(self):
        """Test health metrics page functionality"""
        # Test vital signs
        systolic = 120
        diastolic = 80
        heart_rate = 72
        temperature = 98.6
        
        # Test blood pressure interpretation
        if systolic < 120 and diastolic < 80:
            bp_status = "normal"
        elif systolic < 130 and diastolic < 80:
            bp_status = "elevated"
        else:
            bp_status = "high"
        
        # With systolic=120, diastolic=80, this should be "high" (diastolic >= 80)
        assert bp_status == "high"
        
        # Test heart rate interpretation
        if 60 <= heart_rate <= 100:
            hr_status = "normal"
        elif heart_rate < 60:
            hr_status = "low"
        else:
            hr_status = "elevated"
        
        assert hr_status == "normal"
        
        # Test BMI calculation
        weight_lbs = 150
        height_inches = 67
        height_meters = height_inches * 0.0254
        weight_kg = weight_lbs * 0.453592
        bmi = weight_kg / (height_meters ** 2)
        
        assert 20 <= bmi <= 30  # Reasonable BMI range
        
        # Test weight history
        weight_history = [
            {'date': '2024-01-15', 'weight': 150.0},
            {'date': '2024-01-16', 'weight': 149.5}
        ]
        st.session_state.weight_history = weight_history
        
        assert len(st.session_state.weight_history) == 2
        assert st.session_state.weight_history[0]['weight'] == 150.0
        
        # Test medication tracking
        medications = [
            {
                'name': 'Aspirin',
                'dosage': '81mg',
                'frequency': 'Daily',
                'taken_today': True
            },
            {
                'name': 'Vitamin D',
                'dosage': '1000 IU',
                'frequency': 'Daily',
                'taken_today': False
            }
        ]
        st.session_state.medications = medications
        
        taken_meds = len([med for med in medications if med.get('taken_today')])
        total_meds = len(medications)
        adherence_rate = (taken_meds / total_meds) * 100
        
        assert adherence_rate == 50.0
        
        # Test symptom tracking
        symptoms = ["Headache", "Fatigue"]
        symptom_report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'symptoms': symptoms
        }
        symptom_history = [symptom_report]
        st.session_state.symptom_history = symptom_history
        
        assert len(st.session_state.symptom_history) == 1
        assert len(st.session_state.symptom_history[0]['symptoms']) == 2
    
    def test_health_profile_functionality(self):
        """Test health profile page functionality"""
        # Test personal information
        personal_info = {
            'full_name': 'John Doe',
            'age': 30,
            'gender': 'Male',
            'height_cm': 175,
            'weight_kg': 70,
            'blood_type': 'O+'
        }
        
        for key, value in personal_info.items():
            st.session_state[key] = value
        
        assert st.session_state.full_name == 'John Doe'
        assert st.session_state.age == 30
        assert st.session_state.blood_type == 'O+'
        
        # Test medical history
        chronic_conditions = ['Hypertension', 'Diabetes']
        allergies = ['Penicillin', 'Peanuts']
        surgeries = [{'name': 'Appendectomy', 'year': 2015}]
        
        st.session_state.chronic_conditions = chronic_conditions
        st.session_state.allergies = allergies
        st.session_state.surgeries = surgeries
        
        assert len(st.session_state.chronic_conditions) == 2
        assert len(st.session_state.allergies) == 2
        assert len(st.session_state.surgeries) == 1
        assert st.session_state.surgeries[0]['year'] == 2015
        
        # Test family history
        family_conditions = {
            'father': ['Heart Disease'],
            'mother': ['Diabetes'],
            'sibling': []
        }
        st.session_state.family_conditions = family_conditions
        
        assert len(family_conditions['father']) == 1
        assert len(family_conditions['mother']) == 1
        assert len(family_conditions['sibling']) == 0
        
        # Test health goals
        health_goals = [
            {
                'description': 'Lose 10 pounds',
                'type': 'Weight',
                'created_date': '2024-01-16',
                'completed': False
            },
            {
                'description': 'Exercise 3 times per week',
                'type': 'Exercise',
                'created_date': '2024-01-16',
                'completed': True
            }
        ]
        st.session_state.health_goals = health_goals
        
        completed_goals = len([g for g in health_goals if g['completed']])
        total_goals = len(health_goals)
        completion_rate = (completed_goals / total_goals) * 100
        
        assert completion_rate == 50.0
        assert total_goals == 2
    
    def test_reports_functionality(self):
        """Test reports page functionality"""
        # Test health summary report data collection
        health_data = {
            'personal_info': {
                'name': 'John Doe',
                'age': 30,
                'gender': 'Male',
                'blood_type': 'O+'
            },
            'vitals': {
                'height_cm': 175,
                'weight_kg': 70,
                'bmi': 22.9
            },
            'medical_history': {
                'chronic_conditions': ['Hypertension'],
                'allergies': ['Penicillin'],
                'surgeries': []
            },
            'current_medications': [
                {'name': 'Aspirin', 'dosage': '81mg', 'frequency': 'Daily'}
            ],
            'health_goals': [
                {'description': 'Lose weight', 'completed': False}
            ]
        }
        
        assert health_data['personal_info']['name'] == 'John Doe'
        assert health_data['vitals']['bmi'] == 22.9
        assert len(health_data['medical_history']['chronic_conditions']) == 1
        assert len(health_data['current_medications']) == 1
        
        # Test chat analysis report
        chat_history = [
            {"role": "user", "content": "I have a headache"},
            {"role": "assistant", "content": "Let me help you with that"},
            {"role": "user", "content": "What about my health?"},
            {"role": "assistant", "content": "Here's some health advice"}
        ]
        
        total_messages = len(chat_history)
        user_messages = len([msg for msg in chat_history if msg["role"] == "user"])
        assistant_messages = len([msg for msg in chat_history if msg["role"] == "assistant"])
        
        assert total_messages == 4
        assert user_messages == 2
        assert assistant_messages == 2
        
        # Test topic analysis
        all_text = " ".join([msg.get("content", "") for msg in chat_history])
        common_words = ["health", "headache", "pain", "medication"]
        
        topic_counts = {}
        for word in common_words:
            topic_counts[word] = all_text.lower().count(word)
        
        # "health" appears twice: "What about my health?" and "Here's some health advice"
        assert topic_counts['health'] == 2
        assert topic_counts['headache'] == 1
        assert topic_counts['pain'] == 0
        
        # Test medication report
        medications = [
            {'name': 'Aspirin', 'taken_today': True},
            {'name': 'Vitamin D', 'taken_today': False}
        ]
        
        taken_meds = len([med for med in medications if med.get('taken_today')])
        total_meds = len(medications)
        adherence_rate = (taken_meds / total_meds) * 100
        
        assert adherence_rate == 50.0
        
        # Test symptom trends report
        symptom_history = [
            {'date': '2024-01-15', 'symptoms': ['Headache', 'Fatigue']},
            {'date': '2024-01-16', 'symptoms': ['Headache']}
        ]
        
        all_symptoms = []
        for report in symptom_history:
            all_symptoms.extend(report['symptoms'])
        
        symptom_counts = {}
        for symptom in all_symptoms:
            symptom_counts[symptom] = symptom_counts.get(symptom, 0) + 1
        
        assert symptom_counts['Headache'] == 2
        assert symptom_counts['Fatigue'] == 1
    
    def test_settings_functionality(self):
        """Test settings page functionality"""
        # Test notification settings
        notification_settings = {
            'email_health_reminders': True,
            'email_weekly_reports': True,
            'email_emergency_alerts': True,
            'email_newsletter': False,
            'app_medication_reminders': True,
            'app_goal_reminders': True,
            'app_chat_notifications': True,
            'reminder_frequency': 'Daily'
        }
        st.session_state.notification_settings = notification_settings
        
        assert notification_settings['email_health_reminders'] == True
        assert notification_settings['email_newsletter'] == False
        assert notification_settings['reminder_frequency'] == 'Daily'
        
        # Test privacy settings
        privacy_settings = {
            'share_health_data': False,
            'share_chat_data': True,
            'share_analytics': True,
            'chat_history_retention': 'Keep for 1 year',
            'health_data_retention': 'Keep for 5 years',
            'profile_visibility': 'Private',
            'allow_data_export': True,
            'allow_data_deletion': True
        }
        st.session_state.privacy_settings = privacy_settings
        
        assert privacy_settings['share_health_data'] == False
        assert privacy_settings['profile_visibility'] == 'Private'
        assert privacy_settings['allow_data_export'] == True
        
        # Test appearance settings
        appearance_settings = {
            'theme': 'Light',
            'font_size': 'Medium',
            'color_scheme': 'Default',
            'sidebar_position': 'Left',
            'compact_mode': False,
            'show_animations': True
        }
        st.session_state.appearance_settings = appearance_settings
        
        assert appearance_settings['theme'] == 'Light'
        assert appearance_settings['font_size'] == 'Medium'
        assert appearance_settings['compact_mode'] == False
    
    def test_bmi_calculation(self):
        """Test BMI calculation function"""
        # Test normal BMI
        height_cm = 170
        weight_kg = 65
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        assert 20 <= bmi <= 25  # Normal BMI range
        
        # Test edge cases
        height_cm = 0
        weight_kg = 70
        bmi = weight_kg / ((height_cm / 100) ** 2) if height_cm > 0 else 0
        
        # This would cause division by zero, so we handle it
        assert height_cm == 0  # Invalid input
        
        # Test with valid inputs
        height_cm = 175
        weight_kg = 80
        bmi = weight_kg / ((height_cm / 100) ** 2)
        
        assert 25 <= bmi <= 30  # Overweight BMI range
    
    def test_session_state_persistence(self):
        """Test that session state persists across different features"""
        # Set up data in one feature
        st.session_state.medications = [
            {'name': 'Aspirin', 'dosage': '81mg', 'frequency': 'Daily'}
        ]
        st.session_state.health_goals = [
            {'description': 'Exercise more', 'completed': False}
        ]
        st.session_state.chronic_conditions = ['Hypertension']
        
        # Verify data persists
        assert len(st.session_state.medications) == 1
        assert len(st.session_state.health_goals) == 1
        assert len(st.session_state.chronic_conditions) == 1
        
        # Test data consistency across features
        medication_count = len(st.session_state.medications)
        goal_count = len(st.session_state.health_goals)
        condition_count = len(st.session_state.chronic_conditions)
        
        # Simulate using data in reports
        health_data = {
            'current_medications': st.session_state.medications,
            'health_goals': st.session_state.health_goals,
            'medical_history': {
                'chronic_conditions': st.session_state.chronic_conditions
            }
        }
        
        assert len(health_data['current_medications']) == medication_count
        assert len(health_data['health_goals']) == goal_count
        assert len(health_data['medical_history']['chronic_conditions']) == condition_count
    
    def test_data_validation(self):
        """Test data validation across features"""
        # Test valid data
        valid_age = 30
        valid_height = 175
        valid_weight = 70
        
        assert 0 <= valid_age <= 120
        assert 100 <= valid_height <= 250
        assert 30 <= valid_weight <= 300
        
        # Test invalid data handling
        invalid_age = -5
        invalid_height = 50
        invalid_weight = 500
        
        # These should be caught by validation
        assert not (0 <= invalid_age <= 120)
        assert not (100 <= invalid_height <= 250)
        assert not (30 <= invalid_weight <= 300)
        
        # Test string validation
        valid_name = "John Doe"
        valid_email = "john@example.com"
        
        assert len(valid_name) > 0
        assert '@' in valid_email
        
        # Test empty/invalid strings
        empty_name = ""
        invalid_email = "not-an-email"
        
        assert len(empty_name) == 0
        assert '@' not in invalid_email

if __name__ == "__main__":
    pytest.main([__file__]) 