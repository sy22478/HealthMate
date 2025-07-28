"""
Notification Models for HealthMate Application

This module provides database models for:
- Notification records
- Notification templates
- Delivery tracking
- User notification preferences
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from app.base import Base
from app.utils.encryption_utils import field_encryption


class NotificationType(str, Enum):
    """Types of notifications that can be sent."""
    HEALTH_ALERT = "health_alert"
    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    SYSTEM_NOTIFICATION = "system_notification"
    CHAT_MESSAGE = "chat_message"
    GOAL_ACHIEVEMENT = "goal_achievement"
    EMERGENCY_ALERT = "emergency_alert"
    WEEKLY_SUMMARY = "weekly_summary"
    MONTHLY_REPORT = "monthly_report"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"


class NotificationStatus(str, Enum):
    """Status of notification delivery."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"


class Notification(Base):
    """Model for storing notification records."""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL)
    
    # Channel and delivery
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING)
    
    # Template and metadata
    template_id = Column(String(100), nullable=True)
    template_data = Column(JSON, nullable=True)  # Data used to populate template
    
    # Delivery tracking
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # External service tracking
    external_message_id = Column(String(255), nullable=True)  # ID from email/SMS service
    external_status = Column(String(100), nullable=True)  # Status from external service
    
    # Additional data
    notification_metadata = Column(JSON, nullable=True)  # Additional data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    delivery_attempts = relationship("NotificationDeliveryAttempt", back_populates="notification", cascade="all, delete-orphan")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving."""
        sensitive_fields = ['message', 'failure_reason']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display."""
        sensitive_fields = ['message', 'failure_reason']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert notification to dictionary."""
        if include_sensitive:
            self.decrypt_sensitive_fields()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value if self.type else None,
            'title': self.title,
            'message': self.message if include_sensitive else None,
            'priority': self.priority.value if self.priority else None,
            'channel': self.channel.value if self.channel else None,
            'status': self.status.value if self.status else None,
            'template_id': self.template_id,
            'template_data': self.template_data,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'failure_reason': self.failure_reason if include_sensitive else None,
            'external_message_id': self.external_message_id,
            'external_status': self.external_status,
            'metadata': self.notification_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationTemplate(Base):
    """Model for storing notification templates."""
    __tablename__ = "notification_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template content
    type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    subject = Column(String(255), nullable=True)  # For email templates
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # HTML content for email, text for SMS
    
    # Template configuration
    is_active = Column(Boolean, default=True)
    version = Column(String(20), default="1.0")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert template to dictionary."""
        return {
            'id': self.id,
            'template_id': self.template_id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value if self.type else None,
            'channel': self.channel.value if self.channel else None,
            'subject': self.subject,
            'title': self.title,
            'content': self.content,
            'is_active': self.is_active,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationDeliveryAttempt(Base):
    """Model for tracking delivery attempts."""
    __tablename__ = "notification_delivery_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(Integer, ForeignKey("notifications.id"), nullable=False)
    
    # Attempt details
    attempt_number = Column(Integer, default=1)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    
    # Delivery status
    status = Column(SQLEnum(NotificationStatus), nullable=False)
    external_message_id = Column(String(255), nullable=True)
    external_status = Column(String(100), nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    
    # Timing
    attempted_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    notification = relationship("Notification", back_populates="delivery_attempts")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving."""
        sensitive_fields = ['error_message']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display."""
        sensitive_fields = ['error_message']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert delivery attempt to dictionary."""
        if include_sensitive:
            self.decrypt_sensitive_fields()
        
        return {
            'id': self.id,
            'notification_id': self.notification_id,
            'attempt_number': self.attempt_number,
            'channel': self.channel.value if self.channel else None,
            'status': self.status.value if self.status else None,
            'external_message_id': self.external_message_id,
            'external_status': self.external_status,
            'error_message': self.error_message if include_sensitive else None,
            'error_code': self.error_code,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


class UserNotificationPreference(Base):
    """Model for storing user notification preferences."""
    __tablename__ = "user_notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    push_enabled = Column(Boolean, default=True)
    
    # Type-specific preferences
    preferences = Column(JSON, default=dict)  # Detailed preferences per notification type
    
    # Frequency controls
    max_daily_notifications = Column(Integer, default=10)
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)  # HH:MM format
    timezone = Column(String(50), default="UTC")
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_preferences")
    
    def to_dict(self):
        """Convert preferences to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email_enabled': self.email_enabled,
            'sms_enabled': self.sms_enabled,
            'push_enabled': self.push_enabled,
            'preferences': self.preferences,
            'max_daily_notifications': self.max_daily_notifications,
            'quiet_hours_start': self.quiet_hours_start,
            'quiet_hours_end': self.quiet_hours_end,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class NotificationBounce(Base):
    """Model for tracking email bounces and unsubscribes."""
    __tablename__ = "notification_bounces"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Bounce details
    email = Column(String(255), nullable=False)
    bounce_type = Column(String(50), nullable=False)  # hard, soft, unsubscribe, complaint
    bounce_reason = Column(Text, nullable=True)
    
    # External service data
    external_message_id = Column(String(255), nullable=True)
    external_bounce_id = Column(String(255), nullable=True)
    
    # Metadata
    occurred_at = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)
    
    # Relationships
    user = relationship("User")
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._encrypt_sensitive_fields()
    
    def _encrypt_sensitive_fields(self):
        """Encrypt sensitive fields before saving."""
        sensitive_fields = ['email', 'bounce_reason']
        field_encryption.encrypt_model_fields(self, sensitive_fields)
    
    def decrypt_sensitive_fields(self):
        """Decrypt sensitive fields for display."""
        sensitive_fields = ['email', 'bounce_reason']
        field_encryption.decrypt_model_fields(self, sensitive_fields)
    
    def to_dict(self, include_sensitive=False):
        """Convert bounce to dictionary."""
        if include_sensitive:
            self.decrypt_sensitive_fields()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email if include_sensitive else None,
            'bounce_type': self.bounce_type,
            'bounce_reason': self.bounce_reason if include_sensitive else None,
            'external_message_id': self.external_message_id,
            'external_bounce_id': self.external_bounce_id,
            'occurred_at': self.occurred_at.isoformat() if self.occurred_at else None,
            'processed': self.processed
        } 