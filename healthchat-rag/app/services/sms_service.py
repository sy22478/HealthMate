"""
SMS Notification Service for HealthMate Application

This module provides:
- SMS sending via multiple providers (Twilio, AWS SNS)
- SMS template rendering
- SMS delivery tracking and confirmation
- SMS opt-in/opt-out management
"""

import os
import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    NotificationStatus, NotificationChannel, UserNotificationPreference
)
from app.models.user import User
from app.exceptions.notification_exceptions import SMSError
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class SMSService:
    """Service for sending SMS notifications."""
    
    def __init__(self, settings: Settings):
        """Initialize the SMS service."""
        self.settings = settings
        self.audit_logger = AuditLogger()
        
        # Initialize provider
        self.provider = self._initialize_provider()
        self.client = self._initialize_client()
        
        logger.info(f"SMS service initialized with provider: {settings.sms_provider}")
    
    def _initialize_provider(self):
        """Initialize the SMS provider based on configuration."""
        provider = self.settings.sms_provider.lower()
        
        if provider == "twilio":
            if not TWILIO_AVAILABLE:
                raise SMSError("Twilio not available. Install with: pip install twilio")
            if not all([self.settings.twilio_account_sid, self.settings.twilio_auth_token, self.settings.twilio_phone_number]):
                raise SMSError("Twilio configuration incomplete")
            return "twilio"
        
        elif provider == "aws_sns":
            if not AWS_AVAILABLE:
                raise SMSError("AWS SDK not available. Install with: pip install boto3")
            return "aws_sns"
        
        else:
            raise SMSError(f"Unsupported SMS provider: {provider}")
    
    def _initialize_client(self):
        """Initialize the SMS client based on provider."""
        if self.provider == "twilio":
            return Client(self.settings.twilio_account_sid, self.settings.twilio_auth_token)
        elif self.provider == "aws_sns":
            return boto3.client("sns")
        else:
            return None
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format.
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Basic phone number validation (E.164 format)
        pattern = r'^\+[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number))
    
    def format_phone_number(self, phone_number: str) -> str:
        """
        Format phone number to E.164 format.
        
        Args:
            phone_number: Phone number to format
            
        Returns:
            Formatted phone number
        """
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone_number)
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            # Assume US number if no country code
            if len(cleaned) == 10:
                cleaned = '+1' + cleaned
            else:
                cleaned = '+' + cleaned
        
        return cleaned
    
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        from_phone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an SMS using the configured provider.
        
        Args:
            to_phone: Recipient phone number
            message: SMS message content
            from_phone: Sender phone number (optional)
            metadata: Additional metadata for tracking
            
        Returns:
            Dictionary with delivery status and message ID
        """
        try:
            # Validate and format phone number
            if not self.validate_phone_number(to_phone):
                to_phone = self.format_phone_number(to_phone)
                if not self.validate_phone_number(to_phone):
                    raise SMSError(f"Invalid phone number format: {to_phone}")
            
            # Use default sender if not specified
            from_phone = from_phone or self.settings.twilio_phone_number
            
            # Check message length
            if len(message) > 1600:  # Twilio limit for long messages
                logger.warning(f"SMS message exceeds recommended length: {len(message)} characters")
            
            # Send SMS based on provider
            if self.provider == "twilio":
                result = await self._send_via_twilio(to_phone, message, from_phone)
            elif self.provider == "aws_sns":
                result = await self._send_via_aws_sns(to_phone, message, from_phone)
            else:
                raise SMSError(f"Unsupported provider: {self.provider}")
            
            # Log successful SMS
            self.audit_logger.log_system_action(
                action="sms_sent",
                details={
                    "to_phone": to_phone,
                    "message_length": len(message),
                    "provider": self.provider,
                    "message_id": result.get("message_id"),
                    "metadata": metadata
                }
            )
            
            logger.info(f"SMS sent successfully to {to_phone}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            
            # Log failed SMS
            self.audit_logger.log_system_action(
                action="sms_failed",
                details={
                    "to_phone": to_phone,
                    "provider": self.provider,
                    "error": str(e),
                    "metadata": metadata
                }
            )
            
            raise SMSError(f"Failed to send SMS: {e}", phone_number=to_phone)
    
    async def _send_via_twilio(
        self,
        to_phone: str,
        message: str,
        from_phone: str
    ) -> Dict[str, Any]:
        """Send SMS via Twilio."""
        try:
            message_obj = self.client.messages.create(
                body=message,
                from_=from_phone,
                to=to_phone
            )
            
            return {
                "success": True,
                "message_id": message_obj.sid,
                "status": message_obj.status,
                "provider": "twilio",
                "price": message_obj.price,
                "price_unit": message_obj.price_unit
            }
            
        except TwilioException as e:
            raise SMSError(f"Twilio error: {e}", phone_number=to_phone)
    
    async def _send_via_aws_sns(
        self,
        to_phone: str,
        message: str,
        from_phone: str
    ) -> Dict[str, Any]:
        """Send SMS via AWS SNS."""
        try:
            response = self.client.publish(
                PhoneNumber=to_phone,
                Message=message,
                MessageAttributes={
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional'
                    }
                }
            )
            
            return {
                "success": True,
                "message_id": response["MessageId"],
                "status": "published",
                "provider": "aws_sns"
            }
            
        except ClientError as e:
            raise SMSError(f"AWS SNS error: {e}", phone_number=to_phone)
    
    def render_template(
        self,
        template_name: str,
        template_data: Dict[str, Any]
    ) -> str:
        """
        Render an SMS template with provided data.
        
        Args:
            template_name: Name of the template
            template_data: Data to populate the template
            
        Returns:
            Rendered template content
        """
        try:
            # Simple template rendering for SMS
            # In a real implementation, you might use Jinja2 or similar
            template = self._get_sms_template(template_name)
            if not template:
                raise SMSError(f"SMS template not found: {template_name}")
            
            # Simple variable substitution
            rendered = template
            for key, value in template_data.items():
                placeholder = f"{{{{{key}}}}}"
                rendered = rendered.replace(placeholder, str(value))
            
            return rendered
            
        except Exception as e:
            logger.error(f"Failed to render SMS template {template_name}: {e}")
            raise SMSError(f"Template rendering failed: {e}")
    
    def _get_sms_template(self, template_name: str) -> Optional[str]:
        """Get SMS template by name."""
        templates = {
            "health_alert": "🚨 HealthMate Alert: {title}\n\n{message}\n\nPriority: {priority}\n\nView details: {dashboard_url}",
            "medication_reminder": "💊 Medication Reminder\n\nTime to take: {medication_name}\nDosage: {dosage}\n\n{message}\n\nLog taken: {log_url}",
            "appointment_reminder": "📅 Appointment Reminder\n\n{appointment_type} with {provider}\nDate: {date}\nTime: {time}\nLocation: {location}\n\n{message}",
            "emergency_alert": "🚨 EMERGENCY ALERT\n\n{message}\n\nPlease take immediate action or contact emergency services if needed.",
            "weekly_summary": "📊 Weekly Health Summary\n\n{summary}\n\nHealth Score: {health_score}\n\nView full report: {dashboard_url}",
            "goal_achievement": "🎉 Goal Achieved!\n\nCongratulations! You've achieved: {goal_name}\n\n{message}\n\nKeep up the great work!"
        }
        
        return templates.get(template_name)
    
    async def send_notification_sms(
        self,
        notification: Notification,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a notification SMS.
        
        Args:
            notification: Notification object
            db: Database session
            
        Returns:
            Delivery result
        """
        try:
            # Get user phone number
            user = notification.user
            if not user.phone:
                raise SMSError("User has no phone number", user_id=user.id)
            
            # Check if SMS is enabled for user
            prefs = user.notification_preferences
            if prefs and not prefs.sms_enabled:
                raise SMSError("SMS notifications disabled for user", user_id=user.id)
            
            # Get template if specified
            template_data = notification.template_data or {}
            if notification.template_id:
                template = db.query(NotificationTemplate).filter(
                    NotificationTemplate.template_id == notification.template_id,
                    NotificationTemplate.channel == NotificationChannel.SMS,
                    NotificationTemplate.is_active == True
                ).first()
                
                if template:
                    message = self.render_template(
                        template.template_id,
                        {**template_data, "notification": notification}
                    )
                else:
                    # Use default template
                    message = self._create_default_sms(notification, template_data)
            else:
                # Use default template
                message = self._create_default_sms(notification, template_data)
            
            # Send SMS
            result = await self.send_sms(
                to_phone=user.phone,
                message=message,
                metadata={"notification_id": notification.id}
            )
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.external_message_id = result.get("message_id")
            notification.external_status = result.get("status")
            
            # Create delivery attempt record
            delivery_attempt = NotificationDeliveryAttempt(
                notification_id=notification.id,
                channel=NotificationChannel.SMS,
                status=NotificationStatus.SENT,
                external_message_id=result.get("message_id"),
                external_status=str(result.get("status")),
                completed_at=datetime.utcnow()
            )
            
            db.add(delivery_attempt)
            db.commit()
            
            return result
            
        except Exception as e:
            # Update notification status on failure
            notification.status = NotificationStatus.FAILED
            notification.failed_at = datetime.utcnow()
            notification.failure_reason = str(e)
            
            # Create failed delivery attempt record
            delivery_attempt = NotificationDeliveryAttempt(
                notification_id=notification.id,
                channel=NotificationChannel.SMS,
                status=NotificationStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow()
            )
            
            db.add(delivery_attempt)
            db.commit()
            
            raise
    
    def _create_default_sms(self, notification: Notification, template_data: Dict[str, Any]) -> str:
        """Create default SMS message."""
        message = f"{notification.title}\n\n{notification.message}"
        
        if notification.priority.value in ["urgent", "emergency"]:
            message = f"🚨 {message}"
        elif notification.type.value == "medication_reminder":
            message = f"💊 {message}"
        elif notification.type.value == "appointment_reminder":
            message = f"📅 {message}"
        
        # Add action URL if available
        if template_data.get("action_url"):
            message += f"\n\nView details: {template_data['action_url']}"
        
        return message
    
    async def check_delivery_status(self, message_id: str) -> Dict[str, Any]:
        """
        Check SMS delivery status.
        
        Args:
            message_id: Message ID from provider
            
        Returns:
            Delivery status information
        """
        try:
            if self.provider == "twilio":
                message = self.client.messages(message_id).fetch()
                return {
                    "message_id": message.sid,
                    "status": message.status,
                    "error_code": message.error_code,
                    "error_message": message.error_message,
                    "date_sent": message.date_sent,
                    "date_updated": message.date_updated
                }
            elif self.provider == "aws_sns":
                # AWS SNS doesn't provide detailed delivery status via API
                return {
                    "message_id": message_id,
                    "status": "published",
                    "note": "AWS SNS delivery status not available via API"
                }
            else:
                raise SMSError(f"Delivery status check not supported for provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to check delivery status for {message_id}: {e}")
            raise SMSError(f"Delivery status check failed: {e}")
    
    async def process_webhook(self, webhook_data: Dict[str, Any], db: Session) -> None:
        """
        Process SMS webhook from provider.
        
        Args:
            webhook_data: Webhook data from SMS provider
            db: Database session
        """
        try:
            if self.provider == "twilio":
                await self._process_twilio_webhook(webhook_data, db)
            elif self.provider == "aws_sns":
                await self._process_aws_sns_webhook(webhook_data, db)
            else:
                logger.warning(f"Webhook processing not implemented for provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Failed to process SMS webhook: {e}")
    
    async def _process_twilio_webhook(self, webhook_data: Dict[str, Any], db: Session) -> None:
        """Process Twilio webhook."""
        message_sid = webhook_data.get("MessageSid")
        message_status = webhook_data.get("MessageStatus")
        error_code = webhook_data.get("ErrorCode")
        error_message = webhook_data.get("ErrorMessage")
        
        if message_sid:
            # Find delivery attempt by external message ID
            delivery_attempt = db.query(NotificationDeliveryAttempt).filter(
                NotificationDeliveryAttempt.external_message_id == message_sid,
                NotificationDeliveryAttempt.channel == NotificationChannel.SMS
            ).first()
            
            if delivery_attempt:
                # Update delivery status
                if message_status == "delivered":
                    delivery_attempt.status = NotificationStatus.DELIVERED
                    delivery_attempt.completed_at = datetime.utcnow()
                    
                    # Update notification status
                    notification = delivery_attempt.notification
                    notification.status = NotificationStatus.DELIVERED
                    notification.delivered_at = datetime.utcnow()
                    
                elif message_status in ["failed", "undelivered"]:
                    delivery_attempt.status = NotificationStatus.FAILED
                    delivery_attempt.error_code = error_code
                    delivery_attempt.error_message = error_message
                    delivery_attempt.completed_at = datetime.utcnow()
                    
                    # Update notification status
                    notification = delivery_attempt.notification
                    notification.status = NotificationStatus.FAILED
                    notification.failed_at = datetime.utcnow()
                    notification.failure_reason = error_message
                
                db.commit()
                logger.info(f"Updated SMS delivery status: {message_sid} -> {message_status}")
    
    async def _process_aws_sns_webhook(self, webhook_data: Dict[str, Any], db: Session) -> None:
        """Process AWS SNS webhook."""
        # Implementation for AWS SNS webhook processing
        # This would handle SNS notifications for SMS delivery status
        pass
    
    async def opt_out_user(self, phone_number: str, db: Session) -> bool:
        """
        Opt out user from SMS notifications.
        
        Args:
            phone_number: User's phone number
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find user by phone number
            user = db.query(User).filter(User.phone == phone_number).first()
            if not user:
                logger.warning(f"User not found for phone number: {phone_number}")
                return False
            
            # Update notification preferences
            prefs = user.notification_preferences
            if prefs:
                prefs.sms_enabled = False
                db.commit()
                logger.info(f"User {user.id} opted out of SMS notifications")
                return True
            else:
                logger.warning(f"No notification preferences found for user {user.id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to opt out user from SMS: {e}")
            return False
    
    async def opt_in_user(self, phone_number: str, db: Session) -> bool:
        """
        Opt in user to SMS notifications.
        
        Args:
            phone_number: User's phone number
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Find user by phone number
            user = db.query(User).filter(User.phone == phone_number).first()
            if not user:
                logger.warning(f"User not found for phone number: {phone_number}")
                return False
            
            # Update notification preferences
            prefs = user.notification_preferences
            if prefs:
                prefs.sms_enabled = True
                db.commit()
                logger.info(f"User {user.id} opted in to SMS notifications")
                return True
            else:
                logger.warning(f"No notification preferences found for user {user.id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to opt in user to SMS: {e}")
            return False 