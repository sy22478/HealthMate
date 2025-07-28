"""
Push Notification Service for HealthMate Application

This module provides:
- Push notification sending via FCM and APNS
- Device token management
- Push notification scheduling and delivery
- Push notification analytics and tracking
"""

import os
import logging
import json
import base64
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import asyncio

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False

try:
    from apns2.client import APNsClient
    from apns2.payload import Payload
    from apns2.credentials import TokenCredentials
    APNS_AVAILABLE = True
except ImportError:
    APNS_AVAILABLE = False

from sqlalchemy.orm import Session

from app.config import Settings
from app.models.notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    NotificationStatus, NotificationChannel, UserNotificationPreference
)
from app.models.user import User
from app.exceptions.notification_exceptions import NotificationError
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class PushService:
    """Service for sending push notifications."""
    
    def __init__(self, settings: Settings):
        """Initialize the push notification service."""
        self.settings = settings
        self.audit_logger = AuditLogger()
        
        # Initialize provider
        self.provider = self._initialize_provider()
        self.client = self._initialize_client()
        
        logger.info(f"Push notification service initialized with provider: {settings.push_provider}")
    
    def _initialize_provider(self):
        """Initialize the push notification provider based on configuration."""
        provider = self.settings.push_provider.lower()
        
        if provider == "fcm":
            if not FCM_AVAILABLE:
                raise NotificationError("Firebase Admin SDK not available. Install with: pip install firebase-admin")
            if not self.settings.fcm_server_key:
                raise NotificationError("FCM server key not configured")
            return "fcm"
        
        elif provider == "apns":
            if not APNS_AVAILABLE:
                raise NotificationError("APNS library not available. Install with: pip install apns2")
            if not all([self.settings.apns_key_id, self.settings.apns_team_id, self.settings.apns_key_file]):
                raise NotificationError("APNS configuration incomplete")
            return "apns"
        
        else:
            raise NotificationError(f"Unsupported push notification provider: {provider}")
    
    def _initialize_client(self):
        """Initialize the push notification client based on provider."""
        if self.provider == "fcm":
            # Initialize Firebase Admin SDK
            try:
                # Try to get default app
                firebase_admin.get_app()
            except ValueError:
                # Initialize with default credentials
                firebase_admin.initialize_app()
            return None
        
        elif self.provider == "apns":
            # Initialize APNS client
            credentials = TokenCredentials(
                auth_key_path=self.settings.apns_key_file,
                auth_key_id=self.settings.apns_key_id,
                team_id=self.settings.apns_team_id
            )
            return APNsClient(credentials, use_sandbox=not self.settings.is_production)
        
        else:
            return None
    
    async def send_push_notification(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        sound: Optional[str] = None,
        badge: Optional[int] = None,
        priority: str = "high",
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices.
        
        Args:
            device_tokens: List of device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: URL to notification image
            sound: Sound file name
            badge: Badge number
            priority: Notification priority (high/normal)
            ttl: Time to live in seconds
            metadata: Additional metadata for tracking
            
        Returns:
            Dictionary with delivery status and results
        """
        try:
            if not device_tokens:
                raise NotificationError("No device tokens provided")
            
            # Send push notification based on provider
            if self.provider == "fcm":
                result = await self._send_via_fcm(
                    device_tokens, title, body, data, image_url, sound, badge, priority, ttl
                )
            elif self.provider == "apns":
                result = await self._send_via_apns(
                    device_tokens, title, body, data, image_url, sound, badge, priority, ttl
                )
            else:
                raise NotificationError(f"Unsupported provider: {self.provider}")
            
            # Log successful push notification
            self.audit_logger.log_system_action(
                action="push_notification_sent",
                details={
                    "device_count": len(device_tokens),
                    "title": title,
                    "provider": self.provider,
                    "success_count": result.get("success_count", 0),
                    "failure_count": result.get("failure_count", 0),
                    "metadata": metadata
                }
            )
            
            logger.info(f"Push notification sent to {len(device_tokens)} devices")
            return result
            
        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            
            # Log failed push notification
            self.audit_logger.log_system_action(
                action="push_notification_failed",
                details={
                    "device_count": len(device_tokens),
                    "title": title,
                    "provider": self.provider,
                    "error": str(e),
                    "metadata": metadata
                }
            )
            
            raise NotificationError(f"Failed to send push notification: {e}")
    
    async def _send_via_fcm(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        sound: Optional[str] = None,
        badge: Optional[int] = None,
        priority: str = "high",
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send push notification via Firebase Cloud Messaging."""
        try:
            # Prepare notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Prepare Android configuration
            android_config = messaging.AndroidConfig(
                priority=priority,
                notification=messaging.AndroidNotification(
                    title=title,
                    body=body,
                    image=image_url,
                    sound=sound,
                    click_action="FLUTTER_NOTIFICATION_CLICK"
                ),
                data=data or {}
            )
            
            # Prepare APNS configuration
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=title,
                            body=body
                        ),
                        sound=sound,
                        badge=badge,
                        category="HEALTHMATE_NOTIFICATION"
                    ),
                    custom_data=data or {}
                )
            )
            
            # Prepare message
            message = messaging.MulticastMessage(
                notification=notification,
                android=android_config,
                apns=apns_config,
                data=data or {},
                tokens=device_tokens
            )
            
            # Send message
            response = messaging.send_multicast(message)
            
            # Process results
            success_count = response.success_count
            failure_count = response.failure_count
            
            # Get detailed results
            results = []
            for i, result in enumerate(response.responses):
                if result.success:
                    results.append({
                        "token": device_tokens[i],
                        "success": True,
                        "message_id": result.message_id
                    })
                else:
                    results.append({
                        "token": device_tokens[i],
                        "success": False,
                        "error": result.exception
                    })
            
            return {
                "success": True,
                "success_count": success_count,
                "failure_count": failure_count,
                "results": results,
                "provider": "fcm"
            }
            
        except Exception as e:
            raise NotificationError(f"FCM error: {e}")
    
    async def _send_via_apns(
        self,
        device_tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, Any]] = None,
        image_url: Optional[str] = None,
        sound: Optional[str] = None,
        badge: Optional[int] = None,
        priority: str = "high",
        ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Send push notification via Apple Push Notification Service."""
        try:
            # Prepare payload
            payload = Payload(
                alert={
                    "title": title,
                    "body": body
                },
                sound=sound,
                badge=badge,
                custom=data or {}
            )
            
            # Send to each device
            results = []
            success_count = 0
            failure_count = 0
            
            for token in device_tokens:
                try:
                    response = self.client.send_notification(
                        token_hex=token,
                        notification=payload,
                        topic="com.healthmate.app"  # Your app bundle ID
                    )
                    
                    if response.is_successful:
                        results.append({
                            "token": token,
                            "success": True,
                            "message_id": response.message_id
                        })
                        success_count += 1
                    else:
                        results.append({
                            "token": token,
                            "success": False,
                            "error": response.description
                        })
                        failure_count += 1
                        
                except Exception as e:
                    results.append({
                        "token": token,
                        "success": False,
                        "error": str(e)
                    })
                    failure_count += 1
            
            return {
                "success": True,
                "success_count": success_count,
                "failure_count": failure_count,
                "results": results,
                "provider": "apns"
            }
            
        except Exception as e:
            raise NotificationError(f"APNS error: {e}")
    
    async def send_notification_push(
        self,
        notification: Notification,
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a notification via push notification.
        
        Args:
            notification: Notification object
            db: Database session
            
        Returns:
            Delivery result
        """
        try:
            # Get user device tokens
            user = notification.user
            device_tokens = self._get_user_device_tokens(user.id, db)
            
            if not device_tokens:
                raise NotificationError("User has no registered devices", user_id=user.id)
            
            # Check if push notifications are enabled for user
            prefs = user.notification_preferences
            if prefs and not prefs.push_enabled:
                raise NotificationError("Push notifications disabled for user", user_id=user.id)
            
            # Prepare notification data
            data = {
                "notification_id": str(notification.id),
                "type": notification.type.value,
                "priority": notification.priority.value,
                "timestamp": notification.created_at.isoformat()
            }
            
            # Add template data if available
            if notification.template_data:
                data.update(notification.template_data)
            
            # Send push notification
            result = await self.send_push_notification(
                device_tokens=device_tokens,
                title=notification.title,
                body=notification.message,
                data=data,
                priority="high" if notification.priority.value in ["urgent", "emergency"] else "normal",
                metadata={"notification_id": notification.id}
            )
            
            # Update notification status
            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()
            notification.external_message_id = str(result.get("success_count", 0))
            notification.external_status = f"sent_to_{len(device_tokens)}_devices"
            
            # Create delivery attempt record
            delivery_attempt = NotificationDeliveryAttempt(
                notification_id=notification.id,
                channel=NotificationChannel.PUSH,
                status=NotificationStatus.SENT,
                external_message_id=str(result.get("success_count", 0)),
                external_status=f"sent_to_{len(device_tokens)}_devices",
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
                channel=NotificationChannel.PUSH,
                status=NotificationStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow()
            )
            
            db.add(delivery_attempt)
            db.commit()
            
            raise
    
    def _get_user_device_tokens(self, user_id: int, db: Session) -> List[str]:
        """Get device tokens for a user."""
        # This would query a device tokens table
        # For now, return empty list as placeholder
        # In a real implementation, you would have a DeviceToken model
        return []
    
    async def register_device_token(
        self,
        user_id: int,
        device_token: str,
        platform: str,  # ios, android, web
        device_id: Optional[str] = None,
        db: Session = None
    ) -> bool:
        """
        Register a device token for push notifications.
        
        Args:
            user_id: User ID
            device_token: Device token from FCM/APNS
            platform: Device platform
            device_id: Unique device identifier
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would save to a device tokens table
            # For now, just log the registration
            logger.info(f"Device token registered for user {user_id}: {device_token[:20]}...")
            
            # In a real implementation, you would:
            # 1. Check if token already exists
            # 2. Update existing record or create new one
            # 3. Associate with user
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to register device token: {e}")
            return False
    
    async def unregister_device_token(
        self,
        user_id: int,
        device_token: str,
        db: Session = None
    ) -> bool:
        """
        Unregister a device token.
        
        Args:
            user_id: User ID
            device_token: Device token to unregister
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would remove from device tokens table
            logger.info(f"Device token unregistered for user {user_id}: {device_token[:20]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister device token: {e}")
            return False
    
    async def schedule_push_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        scheduled_time: datetime,
        data: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> str:
        """
        Schedule a push notification for later delivery.
        
        Args:
            user_id: User ID
            title: Notification title
            body: Notification body
            scheduled_time: When to send the notification
            data: Additional data
            db: Database session
            
        Returns:
            Scheduled notification ID
        """
        try:
            # This would save to a scheduled notifications table
            # For now, just return a placeholder ID
            scheduled_id = f"scheduled_{datetime.utcnow().timestamp()}"
            
            logger.info(f"Push notification scheduled for user {user_id} at {scheduled_time}")
            
            return scheduled_id
            
        except Exception as e:
            logger.error(f"Failed to schedule push notification: {e}")
            raise NotificationError(f"Failed to schedule push notification: {e}")
    
    async def cancel_scheduled_notification(
        self,
        scheduled_id: str,
        db: Session = None
    ) -> bool:
        """
        Cancel a scheduled push notification.
        
        Args:
            scheduled_id: Scheduled notification ID
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # This would remove from scheduled notifications table
            logger.info(f"Scheduled notification cancelled: {scheduled_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel scheduled notification: {e}")
            return False
    
    async def get_push_analytics(
        self,
        user_id: Optional[int] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get push notification analytics.
        
        Args:
            user_id: Optional user ID to filter by
            start_date: Start date for analytics
            end_date: End date for analytics
            db: Database session
            
        Returns:
            Analytics data
        """
        try:
            # This would query delivery attempts and notifications
            # For now, return placeholder data
            analytics = {
                "total_sent": 0,
                "total_delivered": 0,
                "total_failed": 0,
                "delivery_rate": 0.0,
                "platform_breakdown": {
                    "ios": 0,
                    "android": 0,
                    "web": 0
                },
                "notification_type_breakdown": {},
                "daily_stats": []
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get push analytics: {e}")
            raise NotificationError(f"Failed to get push analytics: {e}") 