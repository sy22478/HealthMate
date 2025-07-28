"""Add enhanced health models and AI interaction models

Revision ID: add_enhanced_health_models
Revises: 949e4b99c611
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_enhanced_health_models'
down_revision = '949e4b99c611'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums first
    gender_enum = postgresql.ENUM('male', 'female', 'other', 'prefer_not_to_say', name='gender')
    gender_enum.create(op.get_bind())
    
    blood_type_enum = postgresql.ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='bloodtype')
    blood_type_enum.create(op.get_bind())
    
    activity_level_enum = postgresql.ENUM('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active', name='activitylevel')
    activity_level_enum.create(op.get_bind())
    
    smoking_status_enum = postgresql.ENUM('never_smoked', 'former_smoker', 'current_smoker', 'occasional_smoker', name='smokingstatus')
    smoking_status_enum.create(op.get_bind())
    
    alcohol_consumption_enum = postgresql.ENUM('never', 'occasional', 'moderate', 'heavy', 'former_drinker', name='alcoholconsumption')
    alcohol_consumption_enum.create(op.get_bind())
    
    medication_status_enum = postgresql.ENUM('active', 'discontinued', 'completed', 'on_hold', name='medicationstatus')
    medication_status_enum.create(op.get_bind())
    
    symptom_severity_enum = postgresql.ENUM('mild', 'moderate', 'severe', 'critical', name='symptomseverity')
    symptom_severity_enum.create(op.get_bind())
    
    health_goal_status_enum = postgresql.ENUM('not_started', 'in_progress', 'completed', 'abandoned', 'on_hold', name='healthgoalstatus')
    health_goal_status_enum.create(op.get_bind())
    
    conversation_type_enum = postgresql.ENUM('general_health', 'symptom_discussion', 'medication_query', 'treatment_plan', 'emergency', name='conversationtype')
    conversation_type_enum.create(op.get_bind())
    
    feedback_type_enum = postgresql.ENUM('positive', 'negative', 'neutral', name='feedbacktype')
    feedback_type_enum.create(op.get_bind())
    
    # Create user_health_profiles table
    op.create_table('user_health_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('muscle_mass_kg', sa.Float(), nullable=True),
        sa.Column('gender', gender_enum, nullable=True),
        sa.Column('blood_type', blood_type_enum, nullable=True),
        sa.Column('ethnicity', sa.String(length=100), nullable=True),
        sa.Column('occupation', sa.String(length=200), nullable=True),
        sa.Column('activity_level', activity_level_enum, nullable=True),
        sa.Column('smoking_status', smoking_status_enum, nullable=True),
        sa.Column('alcohol_consumption', alcohol_consumption_enum, nullable=True),
        sa.Column('exercise_frequency', sa.String(length=50), nullable=True),
        sa.Column('sleep_hours_per_night', sa.Float(), nullable=True),
        sa.Column('primary_care_physician', sa.String(length=200), nullable=True),
        sa.Column('specialist_physicians', sa.Text(), nullable=True),
        sa.Column('hospital_preferences', sa.Text(), nullable=True),
        sa.Column('insurance_provider', sa.String(length=200), nullable=True),
        sa.Column('insurance_policy_number', sa.String(length=100), nullable=True),
        sa.Column('family_medical_history', sa.Text(), nullable=True),
        sa.Column('food_allergies', sa.Text(), nullable=True),
        sa.Column('drug_allergies', sa.Text(), nullable=True),
        sa.Column('environmental_allergies', sa.Text(), nullable=True),
        sa.Column('chronic_conditions', sa.Text(), nullable=True),
        sa.Column('mental_health_conditions', sa.Text(), nullable=True),
        sa.Column('emergency_contacts', sa.Text(), nullable=True),
        sa.Column('advance_directives', sa.Text(), nullable=True),
        sa.Column('organ_donor_status', sa.Boolean(), nullable=True),
        sa.Column('health_goals', sa.Text(), nullable=True),
        sa.Column('treatment_preferences', sa.Text(), nullable=True),
        sa.Column('communication_preferences', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_health_assessment', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_health_profiles_id'), 'user_health_profiles', ['id'], unique=False)
    
    # Create enhanced_medications table
    op.create_table('enhanced_medications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('health_profile_id', sa.Integer(), nullable=False),
        sa.Column('medication_name', sa.String(length=200), nullable=False),
        sa.Column('generic_name', sa.String(length=200), nullable=True),
        sa.Column('medication_type', sa.String(length=100), nullable=True),
        sa.Column('dosage_form', sa.String(length=100), nullable=True),
        sa.Column('strength', sa.String(length=100), nullable=False),
        sa.Column('dosage_instructions', sa.Text(), nullable=False),
        sa.Column('frequency', sa.String(length=100), nullable=False),
        sa.Column('prescribed_by', sa.String(length=200), nullable=True),
        sa.Column('prescription_date', sa.Date(), nullable=True),
        sa.Column('expiry_date', sa.Date(), nullable=True),
        sa.Column('refill_date', sa.Date(), nullable=True),
        sa.Column('refills_remaining', sa.Integer(), nullable=True),
        sa.Column('pharmacy', sa.String(length=200), nullable=True),
        sa.Column('status', medication_status_enum, nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('reason_for_discontinuation', sa.Text(), nullable=True),
        sa.Column('side_effects', sa.Text(), nullable=True),
        sa.Column('effectiveness_rating', sa.Integer(), nullable=True),
        sa.Column('adherence_rate', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('drug_interactions', sa.Text(), nullable=True),
        sa.Column('contraindications', sa.Text(), nullable=True),
        sa.Column('warnings', sa.Text(), nullable=True),
        sa.Column('cost_per_unit', sa.Float(), nullable=True),
        sa.Column('insurance_coverage', sa.Boolean(), nullable=True),
        sa.Column('copay_amount', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['health_profile_id'], ['user_health_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enhanced_medications_id'), 'enhanced_medications', ['id'], unique=False)
    
    # Create medication_dose_logs table
    op.create_table('medication_dose_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('dose_taken', sa.String(length=100), nullable=False),
        sa.Column('scheduled_time', sa.DateTime(), nullable=True),
        sa.Column('actual_time_taken', sa.DateTime(), nullable=False),
        sa.Column('taken_as_prescribed', sa.Boolean(), nullable=True),
        sa.Column('reason_for_deviation', sa.Text(), nullable=True),
        sa.Column('missed_dose', sa.Boolean(), nullable=True),
        sa.Column('side_effects_experienced', sa.Text(), nullable=True),
        sa.Column('effectiveness_rating', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('location_taken', sa.String(length=200), nullable=True),
        sa.Column('taken_with_food', sa.Boolean(), nullable=True),
        sa.Column('other_medications_taken', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['enhanced_medications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dose_logs_id'), 'medication_dose_logs', ['id'], unique=False)
    
    # Create enhanced_symptom_logs table
    op.create_table('enhanced_symptom_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('health_profile_id', sa.Integer(), nullable=False),
        sa.Column('symptom_name', sa.String(length=200), nullable=False),
        sa.Column('symptom_category', sa.String(length=100), nullable=True),
        sa.Column('severity', symptom_severity_enum, nullable=False),
        sa.Column('pain_level', sa.Integer(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=200), nullable=True),
        sa.Column('duration', sa.String(length=100), nullable=True),
        sa.Column('frequency', sa.String(length=100), nullable=True),
        sa.Column('triggers', sa.Text(), nullable=True),
        sa.Column('aggravating_factors', sa.Text(), nullable=True),
        sa.Column('relieving_factors', sa.Text(), nullable=True),
        sa.Column('associated_symptoms', sa.Text(), nullable=True),
        sa.Column('impact_on_daily_activities', sa.String(length=100), nullable=True),
        sa.Column('impact_on_sleep', sa.String(length=100), nullable=True),
        sa.Column('impact_on_mood', sa.String(length=100), nullable=True),
        sa.Column('treatments_tried', sa.Text(), nullable=True),
        sa.Column('treatment_effectiveness', sa.Text(), nullable=True),
        sa.Column('medications_taken', sa.Text(), nullable=True),
        sa.Column('related_conditions', sa.Text(), nullable=True),
        sa.Column('doctor_consulted', sa.Boolean(), nullable=True),
        sa.Column('doctor_notes', sa.Text(), nullable=True),
        sa.Column('emergency_visit', sa.Boolean(), nullable=True),
        sa.Column('onset_time', sa.DateTime(), nullable=True),
        sa.Column('peak_time', sa.DateTime(), nullable=True),
        sa.Column('resolution_time', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['health_profile_id'], ['user_health_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_enhanced_symptom_logs_id'), 'enhanced_symptom_logs', ['id'], unique=False)
    
    # Create health_metrics_aggregations table
    op.create_table('health_metrics_aggregations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('health_profile_id', sa.Integer(), nullable=False),
        sa.Column('aggregation_period', sa.String(length=20), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('avg_blood_pressure_systolic', sa.Float(), nullable=True),
        sa.Column('avg_blood_pressure_diastolic', sa.Float(), nullable=True),
        sa.Column('min_blood_pressure_systolic', sa.Float(), nullable=True),
        sa.Column('max_blood_pressure_systolic', sa.Float(), nullable=True),
        sa.Column('min_blood_pressure_diastolic', sa.Float(), nullable=True),
        sa.Column('max_blood_pressure_diastolic', sa.Float(), nullable=True),
        sa.Column('avg_heart_rate', sa.Float(), nullable=True),
        sa.Column('min_heart_rate', sa.Float(), nullable=True),
        sa.Column('max_heart_rate', sa.Float(), nullable=True),
        sa.Column('resting_heart_rate', sa.Float(), nullable=True),
        sa.Column('avg_weight', sa.Float(), nullable=True),
        sa.Column('weight_change', sa.Float(), nullable=True),
        sa.Column('bmi_trend', sa.Float(), nullable=True),
        sa.Column('avg_blood_sugar', sa.Float(), nullable=True),
        sa.Column('min_blood_sugar', sa.Float(), nullable=True),
        sa.Column('max_blood_sugar', sa.Float(), nullable=True),
        sa.Column('avg_temperature', sa.Float(), nullable=True),
        sa.Column('min_temperature', sa.Float(), nullable=True),
        sa.Column('max_temperature', sa.Float(), nullable=True),
        sa.Column('total_steps', sa.Integer(), nullable=True),
        sa.Column('avg_steps_per_day', sa.Float(), nullable=True),
        sa.Column('total_calories_burned', sa.Float(), nullable=True),
        sa.Column('avg_calories_burned_per_day', sa.Float(), nullable=True),
        sa.Column('total_exercise_minutes', sa.Integer(), nullable=True),
        sa.Column('avg_exercise_minutes_per_day', sa.Float(), nullable=True),
        sa.Column('avg_sleep_hours', sa.Float(), nullable=True),
        sa.Column('total_sleep_hours', sa.Float(), nullable=True),
        sa.Column('sleep_quality_score', sa.Float(), nullable=True),
        sa.Column('medication_adherence_rate', sa.Float(), nullable=True),
        sa.Column('total_medications_taken', sa.Integer(), nullable=True),
        sa.Column('total_medications_scheduled', sa.Integer(), nullable=True),
        sa.Column('missed_doses', sa.Integer(), nullable=True),
        sa.Column('total_symptoms_logged', sa.Integer(), nullable=True),
        sa.Column('avg_symptom_severity', sa.Float(), nullable=True),
        sa.Column('most_common_symptom', sa.String(length=200), nullable=True),
        sa.Column('symptom_frequency', sa.Text(), nullable=True),
        sa.Column('overall_health_score', sa.Float(), nullable=True),
        sa.Column('health_score_trend', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['health_profile_id'], ['user_health_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_metrics_aggregations_id'), 'health_metrics_aggregations', ['id'], unique=False)
    
    # Create conversation_histories table
    op.create_table('conversation_histories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.String(length=100), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_summary', sa.Text(), nullable=True),
        sa.Column('conversation_type', conversation_type_enum, nullable=True),
        sa.Column('context_sources', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('user_feedback', feedback_type_enum, nullable=True),
        sa.Column('feedback_comment', sa.Text(), nullable=True),
        sa.Column('user_rating', sa.Integer(), nullable=True),
        sa.Column('health_context', sa.Text(), nullable=True),
        sa.Column('symptom_mentions', sa.Text(), nullable=True),
        sa.Column('medication_mentions', sa.Text(), nullable=True),
        sa.Column('urgency_level', sa.String(length=20), nullable=True),
        sa.Column('model_used', sa.String(length=100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('processing_metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversation_histories_id'), 'conversation_histories', ['id'], unique=False)
    op.create_index(op.f('ix_conversation_histories_conversation_id'), 'conversation_histories', ['conversation_id'], unique=False)
    
    # Create ai_response_caches table
    op.create_table('ai_response_caches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_hash', sa.String(length=64), nullable=False),
        sa.Column('user_context_hash', sa.String(length=64), nullable=True),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.Column('cached_response', sa.Text(), nullable=False),
        sa.Column('response_metadata', sa.Text(), nullable=True),
        sa.Column('cache_hits', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('response_quality_score', sa.Float(), nullable=True),
        sa.Column('user_satisfaction_score', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_response_caches_id'), 'ai_response_caches', ['id'], unique=False)
    op.create_index(op.f('ix_ai_response_caches_query_hash'), 'ai_response_caches', ['query_hash'], unique=False)
    op.create_index(op.f('ix_ai_response_caches_user_context_hash'), 'ai_response_caches', ['user_context_hash'], unique=False)
    
    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('preferred_language', sa.String(length=10), nullable=True),
        sa.Column('communication_style', sa.String(length=50), nullable=True),
        sa.Column('response_length_preference', sa.String(length=20), nullable=True),
        sa.Column('notification_frequency', sa.String(length=20), nullable=True),
        sa.Column('health_detail_level', sa.String(length=20), nullable=True),
        sa.Column('medical_terminology_level', sa.String(length=20), nullable=True),
        sa.Column('include_statistics', sa.Boolean(), nullable=True),
        sa.Column('include_recommendations', sa.Boolean(), nullable=True),
        sa.Column('data_sharing_level', sa.String(length=20), nullable=True),
        sa.Column('allow_analytics', sa.Boolean(), nullable=True),
        sa.Column('allow_research_use', sa.Boolean(), nullable=True),
        sa.Column('ai_personality', sa.String(length=50), nullable=True),
        sa.Column('conversation_memory_duration', sa.Integer(), nullable=True),
        sa.Column('auto_suggestions', sa.Boolean(), nullable=True),
        sa.Column('proactive_alerts', sa.Boolean(), nullable=True),
        sa.Column('font_size', sa.String(length=20), nullable=True),
        sa.Column('color_scheme', sa.String(length=20), nullable=True),
        sa.Column('screen_reader_support', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_preferences_id'), 'user_preferences', ['id'], unique=False)
    
    # Create user_feedbacks table
    op.create_table('user_feedbacks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('conversation_id', sa.String(length=100), nullable=True),
        sa.Column('response_id', sa.Integer(), nullable=True),
        sa.Column('feedback_type', feedback_type_enum, nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('detailed_feedback', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('user_expectation', sa.Text(), nullable=True),
        sa.Column('actual_outcome', sa.Text(), nullable=True),
        sa.Column('impact_on_health_decision', sa.String(length=50), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('follow_up_needed', sa.Boolean(), nullable=True),
        sa.Column('response_accuracy', sa.Integer(), nullable=True),
        sa.Column('response_helpfulness', sa.Integer(), nullable=True),
        sa.Column('response_clarity', sa.Integer(), nullable=True),
        sa.Column('overall_satisfaction', sa.Integer(), nullable=True),
        sa.Column('follow_up_completed', sa.Boolean(), nullable=True),
        sa.Column('follow_up_notes', sa.Text(), nullable=True),
        sa.Column('resolution_status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_feedbacks_id'), 'user_feedbacks', ['id'], unique=False)
    op.create_index(op.f('ix_user_feedbacks_conversation_id'), 'user_feedbacks', ['conversation_id'], unique=False)


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_user_feedbacks_conversation_id'), table_name='user_feedbacks')
    op.drop_index(op.f('ix_user_feedbacks_id'), table_name='user_feedbacks')
    op.drop_table('user_feedbacks')
    
    op.drop_index(op.f('ix_user_preferences_id'), table_name='user_preferences')
    op.drop_table('user_preferences')
    
    op.drop_index(op.f('ix_ai_response_caches_user_context_hash'), table_name='ai_response_caches')
    op.drop_index(op.f('ix_ai_response_caches_query_hash'), table_name='ai_response_caches')
    op.drop_index(op.f('ix_ai_response_caches_id'), table_name='ai_response_caches')
    op.drop_table('ai_response_caches')
    
    op.drop_index(op.f('ix_conversation_histories_conversation_id'), table_name='conversation_histories')
    op.drop_index(op.f('ix_conversation_histories_id'), table_name='conversation_histories')
    op.drop_table('conversation_histories')
    
    op.drop_index(op.f('ix_health_metrics_aggregations_id'), table_name='health_metrics_aggregations')
    op.drop_table('health_metrics_aggregations')
    
    op.drop_index(op.f('ix_enhanced_symptom_logs_id'), table_name='enhanced_symptom_logs')
    op.drop_table('enhanced_symptom_logs')
    
    op.drop_index(op.f('ix_medication_dose_logs_id'), table_name='medication_dose_logs')
    op.drop_table('medication_dose_logs')
    
    op.drop_index(op.f('ix_enhanced_medications_id'), table_name='enhanced_medications')
    op.drop_table('enhanced_medications')
    
    op.drop_index(op.f('ix_user_health_profiles_id'), table_name='user_health_profiles')
    op.drop_table('user_health_profiles')
    
    # Drop enums
    feedback_type_enum = postgresql.ENUM(name='feedbacktype')
    feedback_type_enum.drop(op.get_bind())
    
    conversation_type_enum = postgresql.ENUM(name='conversationtype')
    conversation_type_enum.drop(op.get_bind())
    
    health_goal_status_enum = postgresql.ENUM(name='healthgoalstatus')
    health_goal_status_enum.drop(op.get_bind())
    
    symptom_severity_enum = postgresql.ENUM(name='symptomseverity')
    symptom_severity_enum.drop(op.get_bind())
    
    medication_status_enum = postgresql.ENUM(name='medicationstatus')
    medication_status_enum.drop(op.get_bind())
    
    alcohol_consumption_enum = postgresql.ENUM(name='alcoholconsumption')
    alcohol_consumption_enum.drop(op.get_bind())
    
    smoking_status_enum = postgresql.ENUM(name='smokingstatus')
    smoking_status_enum.drop(op.get_bind())
    
    activity_level_enum = postgresql.ENUM(name='activitylevel')
    activity_level_enum.drop(op.get_bind())
    
    blood_type_enum = postgresql.ENUM(name='bloodtype')
    blood_type_enum.drop(op.get_bind())
    
    gender_enum = postgresql.ENUM(name='gender')
    gender_enum.drop(op.get_bind()) 