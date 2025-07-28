"""Add notification models

Revision ID: add_notification_models
Revises: add_enhanced_health_models
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_notification_models'
down_revision = 'add_enhanced_health_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create notification_type enum
    notification_type = postgresql.ENUM('health_alert', 'medication_reminder', 'appointment_reminder', 
                                       'system_notification', 'chat_message', 'goal_achievement', 
                                       'emergency_alert', 'weekly_summary', 'monthly_report', 
                                       name='notificationtype')
    notification_type.create(op.get_bind())
    
    # Create notification_priority enum
    notification_priority = postgresql.ENUM('low', 'normal', 'high', 'urgent', 'emergency', 
                                           name='notificationpriority')
    notification_priority.create(op.get_bind())
    
    # Create notification_channel enum
    notification_channel = postgresql.ENUM('email', 'sms', 'push', 'webhook', 
                                          name='notificationchannel')
    notification_channel.create(op.get_bind())
    
    # Create notification_status enum
    notification_status = postgresql.ENUM('pending', 'sent', 'delivered', 'failed', 'bounced', 'unsubscribed', 
                                         name='notificationstatus')
    notification_status.create(op.get_bind())
    
    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('health_alert', 'medication_reminder', 'appointment_reminder', 
                                 'system_notification', 'chat_message', 'goal_achievement', 
                                 'emergency_alert', 'weekly_summary', 'monthly_report', 
                                 name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('priority', sa.Enum('low', 'normal', 'high', 'urgent', 'emergency', 
                                     name='notificationpriority'), nullable=True),
        sa.Column('channel', sa.Enum('email', 'sms', 'push', 'webhook', 
                                    name='notificationchannel'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'failed', 'bounced', 'unsubscribed', 
                                   name='notificationstatus'), nullable=True),
        sa.Column('template_id', sa.String(length=100), nullable=True),
        sa.Column('template_data', sa.JSON(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('failed_at', sa.DateTime(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('external_message_id', sa.String(length=255), nullable=True),
        sa.Column('external_status', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    
    # Create notification_templates table
    op.create_table('notification_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.Enum('health_alert', 'medication_reminder', 'appointment_reminder', 
                                 'system_notification', 'chat_message', 'goal_achievement', 
                                 'emergency_alert', 'weekly_summary', 'monthly_report', 
                                 name='notificationtype'), nullable=False),
        sa.Column('channel', sa.Enum('email', 'sms', 'push', 'webhook', 
                                    name='notificationchannel'), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('version', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('template_id')
    )
    op.create_index(op.f('ix_notification_templates_id'), 'notification_templates', ['id'], unique=False)
    op.create_index(op.f('ix_notification_templates_template_id'), 'notification_templates', ['template_id'], unique=True)
    
    # Create notification_delivery_attempts table
    op.create_table('notification_delivery_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_id', sa.Integer(), nullable=False),
        sa.Column('attempt_number', sa.Integer(), nullable=True),
        sa.Column('channel', sa.Enum('email', 'sms', 'push', 'webhook', 
                                    name='notificationchannel'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'sent', 'delivered', 'failed', 'bounced', 'unsubscribed', 
                                   name='notificationstatus'), nullable=False),
        sa.Column('external_message_id', sa.String(length=255), nullable=True),
        sa.Column('external_status', sa.String(length=100), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(length=100), nullable=True),
        sa.Column('attempted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['notification_id'], ['notifications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_delivery_attempts_id'), 'notification_delivery_attempts', ['id'], unique=False)
    
    # Create user_notification_preferences table
    op.create_table('user_notification_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_enabled', sa.Boolean(), nullable=True),
        sa.Column('sms_enabled', sa.Boolean(), nullable=True),
        sa.Column('push_enabled', sa.Boolean(), nullable=True),
        sa.Column('preferences', sa.JSON(), nullable=True),
        sa.Column('max_daily_notifications', sa.Integer(), nullable=True),
        sa.Column('quiet_hours_start', sa.String(length=5), nullable=True),
        sa.Column('quiet_hours_end', sa.String(length=5), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_notification_preferences_id'), 'user_notification_preferences', ['id'], unique=False)
    
    # Create notification_bounces table
    op.create_table('notification_bounces',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('bounce_type', sa.String(length=50), nullable=False),
        sa.Column('bounce_reason', sa.Text(), nullable=True),
        sa.Column('external_message_id', sa.String(length=255), nullable=True),
        sa.Column('external_bounce_id', sa.String(length=255), nullable=True),
        sa.Column('occurred_at', sa.DateTime(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_bounces_id'), 'notification_bounces', ['id'], unique=False)


def downgrade():
    # Drop tables
    op.drop_index(op.f('ix_notification_bounces_id'), table_name='notification_bounces')
    op.drop_table('notification_bounces')
    
    op.drop_index(op.f('ix_user_notification_preferences_id'), table_name='user_notification_preferences')
    op.drop_table('user_notification_preferences')
    
    op.drop_index(op.f('ix_notification_delivery_attempts_id'), table_name='notification_delivery_attempts')
    op.drop_table('notification_delivery_attempts')
    
    op.drop_index(op.f('ix_notification_templates_template_id'), table_name='notification_templates')
    op.drop_index(op.f('ix_notification_templates_id'), table_name='notification_templates')
    op.drop_table('notification_templates')
    
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    
    # Drop enums
    notification_status = postgresql.ENUM('pending', 'sent', 'delivered', 'failed', 'bounced', 'unsubscribed', 
                                         name='notificationstatus')
    notification_status.drop(op.get_bind())
    
    notification_channel = postgresql.ENUM('email', 'sms', 'push', 'webhook', 
                                          name='notificationchannel')
    notification_channel.drop(op.get_bind())
    
    notification_priority = postgresql.ENUM('low', 'normal', 'high', 'urgent', 'emergency', 
                                           name='notificationpriority')
    notification_priority.drop(op.get_bind())
    
    notification_type = postgresql.ENUM('health_alert', 'medication_reminder', 'appointment_reminder', 
                                       'system_notification', 'chat_message', 'goal_achievement', 
                                       'emergency_alert', 'weekly_summary', 'monthly_report', 
                                       name='notificationtype')
    notification_type.drop(op.get_bind()) 