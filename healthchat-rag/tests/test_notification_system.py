"""
Tests for the Notification System

This module tests:
- Email notification service
- SMS notification service
- Push notification service
- Main notification service
- Notification models
- Template rendering
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    NotificationStatus, NotificationChannel, NotificationType, NotificationPriority,
    UserNotificationPreference, NotificationBounce
)
from app.models.user import User
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.push_service import PushService
from app.services.notification_service import NotificationService, NotificationStrategy
from app.exceptions.notification_exceptions import NotificationError, EmailError, SMSError


class TestNotificationModels:
    """Test notification model functionality."""
    
    def test_notification_creation(self):
        """Test creating a notification."""
        notification = Notification(
            user_id=1,
            type=NotificationType.HEALTH_ALERT,
            title="Test Alert",
            message="This is a test alert",
            priority=NotificationPriority.HIGH,
            channel=NotificationChannel.EMAIL
        )
        
        assert notification.user_id == 1
        assert notification.type == NotificationType.HEALTH_ALERT
        assert notification.title == "Test Alert"
        assert notification.message == "This is a test alert"
        assert notification.priority == NotificationPriority.HIGH
        assert notification.channel == NotificationChannel.EMAIL
        assert notification.status == NotificationStatus.PENDING
    
    def test_notification_to_dict(self):
        """Test notification to_dict method."""
        notification = Notification(
            user_id=1,
            type=NotificationType.MEDICATION_REMINDER,
            title="Medication Reminder",
            message="Time to take your medication",
            priority=NotificationPriority.NORMAL,
            channel=NotificationChannel.SMS
        )
        
        notification_dict = notification.to_dict()
        
        assert notification_dict["user_id"] == 1
        assert notification_dict["type"] == "medication_reminder"
        assert notification_dict["title"] == "Medication Reminder"
        assert notification_dict["priority"] == "normal"
        assert notification_dict["channel"] == "sms"
    
    def test_notification_template_creation(self):
        """Test creating a notification template."""
        template = NotificationTemplate(
            template_id="health_alert_email",
            name="Health Alert Email Template",
            description="Template for health alert emails",
            type=NotificationType.HEALTH_ALERT,
            channel=NotificationChannel.EMAIL,
            subject="Health Alert",
            title="Health Alert",
            content="<h1>{{ title }}</h1><p>{{ message }}</p>"
        )
        
        assert template.template_id == "health_alert_email"
        assert template.name == "Health Alert Email Template"
        assert template.type == NotificationType.HEALTH_ALERT
        assert template.channel == NotificationChannel.EMAIL
        assert template.is_active is True
    
    def test_user_notification_preferences(self):
        """Test user notification preferences."""
        prefs = UserNotificationPreference(
            user_id=1,
            email_enabled=True,
            sms_enabled=False,
            push_enabled=True,
            max_daily_notifications=10,
            timezone="UTC"
        )
        
        assert prefs.user_id == 1
        assert prefs.email_enabled is True
        assert prefs.sms_enabled is False
        assert prefs.push_enabled is True
        assert prefs.max_daily_notifications == 10
        assert prefs.timezone == "UTC"


class TestEmailService:
    """Test email notification service."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            email_provider="smtp",
            smtp_host="localhost",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            email_from_address="noreply@healthmate.com",
            email_from_name="HealthMate"
        )
    
    @pytest.fixture
    def email_service(self, settings):
        """Create email service instance."""
        return EmailService(settings)
    
    def test_email_service_initialization(self, settings):
        """Test email service initialization."""
        service = EmailService(settings)
        assert service.settings == settings
        assert service.provider == "smtp"
    
    @patch('app.services.email_service.SENDGRID_AVAILABLE', True)
    def test_sendgrid_initialization(self):
        """Test SendGrid initialization."""
        settings = Settings(
            email_provider="sendgrid",
            sendgrid_api_key="test_key",
            email_from_address="noreply@healthmate.com",
            email_from_name="HealthMate"
        )
        
        service = EmailService(settings)
        assert service.provider == "sendgrid"
    
    def test_invalid_provider(self):
        """Test invalid email provider."""
        settings = Settings(
            email_provider="invalid",
            email_from_address="noreply@healthmate.com",
            email_from_name="HealthMate"
        )
        
        with pytest.raises(EmailError, match="Unsupported email provider"):
            EmailService(settings)
    
    @pytest.mark.asyncio
    async def test_send_email_smtp(self, email_service):
        """Test sending email via SMTP."""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_service.send_email(
                to_email="user@example.com",
                subject="Test Subject",
                html_content="<h1>Test</h1>",
                text_content="Test"
            )
            
            assert result["success"] is True
            assert result["provider"] == "smtp"
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    def test_html_to_text_conversion(self, email_service):
        """Test HTML to text conversion."""
        html = "<h1>Title</h1><p>This is a <strong>test</strong> message.</p>"
        text = email_service._html_to_text(html)
        
        assert "Title" in text
        assert "This is a test message" in text
        assert "<h1>" not in text
        assert "<strong>" not in text
    
    def test_render_template(self, email_service):
        """Test template rendering."""
        template_data = {
            "user_name": "John Doe",
            "alert_type": "High Blood Pressure"
        }
        
        # This would test actual template rendering
        # For now, just test the method exists
        assert hasattr(email_service, 'render_template')


class TestSMSService:
    """Test SMS notification service."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            sms_provider="twilio",
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            twilio_phone_number="+1234567890"
        )
    
    @pytest.fixture
    def sms_service(self, settings):
        """Create SMS service instance."""
        return SMSService(settings)
    
    def test_sms_service_initialization(self, settings):
        """Test SMS service initialization."""
        service = SMSService(settings)
        assert service.settings == settings
        assert service.provider == "twilio"
    
    def test_phone_number_validation(self, sms_service):
        """Test phone number validation."""
        # Valid phone numbers
        assert sms_service.validate_phone_number("+1234567890") is True
        assert sms_service.validate_phone_number("+44123456789") is True
        
        # Invalid phone numbers
        assert sms_service.validate_phone_number("1234567890") is False
        assert sms_service.validate_phone_number("invalid") is False
        assert sms_service.validate_phone_number("") is False
    
    def test_phone_number_formatting(self, sms_service):
        """Test phone number formatting."""
        # US number without country code
        formatted = sms_service.format_phone_number("1234567890")
        assert formatted == "+11234567890"
        
        # Number with country code
        formatted = sms_service.format_phone_number("+44123456789")
        assert formatted == "+44123456789"
        
        # Number with spaces and dashes
        formatted = sms_service.format_phone_number("123-456-7890")
        assert formatted == "+11234567890"
    
    @pytest.mark.asyncio
    async def test_send_sms_twilio(self, sms_service):
        """Test sending SMS via Twilio."""
        with patch('app.services.sms_service.TWILIO_AVAILABLE', True):
            with patch('twilio.rest.Client') as mock_client:
                mock_message = Mock()
                mock_message.sid = "test_sid"
                mock_message.status = "sent"
                mock_message.price = "0.01"
                mock_message.price_unit = "USD"
                
                mock_client.return_value.messages.create.return_value = mock_message
                
                result = await sms_service.send_sms(
                    to_phone="+1234567890",
                    message="Test SMS message"
                )
                
                assert result["success"] is True
                assert result["message_id"] == "test_sid"
                assert result["provider"] == "twilio"
    
    def test_sms_template_rendering(self, sms_service):
        """Test SMS template rendering."""
        template_name = "health_alert"
        template_data = {
            "title": "Health Alert",
            "message": "Your blood pressure is high",
            "priority": "high",
            "dashboard_url": "https://healthmate.com/dashboard"
        }
        
        result = sms_service.render_template(template_name, template_data)
        
        assert "HealthMate Alert" in result
        assert "Health Alert" in result
        assert "Your blood pressure is high" in result
        assert "https://healthmate.com/dashboard" in result


class TestPushService:
    """Test push notification service."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            push_provider="fcm",
            fcm_server_key="test_key"
        )
    
    @pytest.fixture
    def push_service(self, settings):
        """Create push service instance."""
        return PushService(settings)
    
    def test_push_service_initialization(self, settings):
        """Test push service initialization."""
        service = PushService(settings)
        assert service.settings == settings
        assert service.provider == "fcm"
    
    @pytest.mark.asyncio
    async def test_send_push_notification_fcm(self, push_service):
        """Test sending push notification via FCM."""
        with patch('app.services.push_service.FCM_AVAILABLE', True):
            with patch('firebase_admin.messaging.send_multicast') as mock_send:
                mock_response = Mock()
                mock_response.success_count = 1
                mock_response.failure_count = 0
                mock_response.responses = [Mock(success=True, message_id="test_id")]
                mock_send.return_value = mock_response
                
                result = await push_service.send_push_notification(
                    device_tokens=["test_token"],
                    title="Test Title",
                    body="Test Body"
                )
                
                assert result["success"] is True
                assert result["success_count"] == 1
                assert result["failure_count"] == 0
                assert result["provider"] == "fcm"
    
    def test_get_user_device_tokens(self, push_service):
        """Test getting user device tokens."""
        # This would test actual device token retrieval
        # For now, just test the method exists
        assert hasattr(push_service, '_get_user_device_tokens')


class TestNotificationService:
    """Test main notification service."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            email_provider="smtp",
            smtp_host="localhost",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            email_from_address="noreply@healthmate.com",
            email_from_name="HealthMate",
            sms_provider="twilio",
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            twilio_phone_number="+1234567890",
            push_provider="fcm",
            fcm_server_key="test_key"
        )
    
    @pytest.fixture
    def notification_service(self, settings):
        """Create notification service instance."""
        return NotificationService(settings)
    
    def test_notification_service_initialization(self, settings):
        """Test notification service initialization."""
        service = NotificationService(settings)
        assert service.settings == settings
        assert service.email_service is not None
        assert service.sms_service is not None
        assert service.push_service is not None
    
    def test_determine_channels_all_channels(self, notification_service):
        """Test determining channels with ALL_CHANNELS strategy."""
        user = Mock()
        user.notification_preferences = Mock()
        user.notification_preferences.email_enabled = True
        user.notification_preferences.sms_enabled = True
        user.notification_preferences.push_enabled = True
        
        channels = notification_service._determine_channels(
            user,
            NotificationType.HEALTH_ALERT,
            NotificationPriority.NORMAL,
            NotificationStrategy.ALL_CHANNELS
        )
        
        assert NotificationChannel.EMAIL in channels
        assert NotificationChannel.SMS in channels
        assert NotificationChannel.PUSH in channels
    
    def test_determine_channels_preferred_channel(self, notification_service):
        """Test determining channels with PREFERRED_CHANNEL strategy."""
        user = Mock()
        user.notification_preferences = Mock()
        user.notification_preferences.email_enabled = True
        user.notification_preferences.preferences = {
            "health_alert": {"preferred_channel": "email"}
        }
        
        channels = notification_service._determine_channels(
            user,
            NotificationType.HEALTH_ALERT,
            NotificationPriority.NORMAL,
            NotificationStrategy.PREFERRED_CHANNEL
        )
        
        assert channels == [NotificationChannel.EMAIL]
    
    def test_smart_routing_emergency(self, notification_service):
        """Test smart routing for emergency notifications."""
        user = Mock()
        user.notification_preferences = Mock()
        user.notification_preferences.sms_enabled = True
        user.notification_preferences.push_enabled = True
        user.notification_preferences.email_enabled = True
        
        channels = notification_service._smart_route_notification(
            user,
            NotificationType.EMERGENCY_ALERT,
            NotificationPriority.EMERGENCY
        )
        
        # SMS should be first for emergencies
        assert channels[0] == NotificationChannel.SMS
        assert NotificationChannel.PUSH in channels
        assert NotificationChannel.EMAIL in channels
    
    def test_smart_routing_medication_reminder(self, notification_service):
        """Test smart routing for medication reminders."""
        user = Mock()
        user.notification_preferences = Mock()
        user.notification_preferences.sms_enabled = True
        user.notification_preferences.push_enabled = True
        user.notification_preferences.email_enabled = True
        
        channels = notification_service._smart_route_notification(
            user,
            NotificationType.MEDICATION_REMINDER,
            NotificationPriority.NORMAL
        )
        
        # SMS should be preferred for medication reminders
        assert channels[0] == NotificationChannel.SMS
    
    @pytest.mark.asyncio
    async def test_send_notification(self, notification_service):
        """Test sending a notification."""
        # Mock database session
        db = Mock()
        
        # Mock user
        user = Mock()
        user.id = 1
        user.notification_preferences = Mock()
        user.notification_preferences.email_enabled = True
        
        # Mock database query
        db.query.return_value.filter.return_value.first.return_value = user
        
        # Mock email service
        notification_service.email_service.send_notification_email = AsyncMock()
        notification_service.email_service.send_notification_email.return_value = {
            "success": True,
            "message_id": "test_id"
        }
        
        result = await notification_service.send_notification(
            user_id=1,
            notification_type=NotificationType.HEALTH_ALERT,
            title="Test Alert",
            message="Test message",
            priority=NotificationPriority.NORMAL,
            db=db
        )
        
        assert result["user_id"] == 1
        assert result["success"] is True
        assert "email" in result["results"]
    
    @pytest.mark.asyncio
    async def test_send_bulk_notifications(self, notification_service):
        """Test sending bulk notifications."""
        # Mock database session
        db = Mock()
        
        # Mock user
        user = Mock()
        user.id = 1
        user.notification_preferences = Mock()
        user.notification_preferences.email_enabled = True
        
        # Mock database query
        db.query.return_value.filter.return_value.first.return_value = user
        
        # Mock email service
        notification_service.email_service.send_notification_email = AsyncMock()
        notification_service.email_service.send_notification_email.return_value = {
            "success": True,
            "message_id": "test_id"
        }
        
        result = await notification_service.send_bulk_notifications(
            user_ids=[1, 2, 3],
            notification_type=NotificationType.HEALTH_ALERT,
            title="Test Alert",
            message="Test message",
            db=db
        )
        
        assert result["total_users"] == 3
        assert result["successful"] == 3
        assert result["failed"] == 0


class TestNotificationIntegration:
    """Integration tests for the notification system."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            email_provider="smtp",
            smtp_host="localhost",
            smtp_port=587,
            smtp_username="test@example.com",
            smtp_password="password",
            email_from_address="noreply@healthmate.com",
            email_from_name="HealthMate",
            sms_provider="twilio",
            twilio_account_sid="test_sid",
            twilio_auth_token="test_token",
            twilio_phone_number="+1234567890",
            push_provider="fcm",
            fcm_server_key="test_key"
        )
    
    @pytest.mark.asyncio
    async def test_full_notification_flow(self, settings):
        """Test the full notification flow."""
        # This would test the complete flow from notification creation
        # to delivery across all channels
        pass
    
    @pytest.mark.asyncio
    async def test_notification_preferences_management(self, settings):
        """Test notification preferences management."""
        # This would test updating and retrieving user preferences
        pass
    
    @pytest.mark.asyncio
    async def test_notification_analytics(self, settings):
        """Test notification analytics."""
        # This would test analytics collection and reporting
        pass


if __name__ == "__main__":
    pytest.main([__file__]) 