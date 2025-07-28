"""
Main Notification Service for HealthMate Application

This module provides:
- Unified notification sending across all channels
- Smart notification routing and prioritization
- Notification queue management
- Delivery tracking and analytics
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.config import Settings
from app.models.notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    NotificationStatus, NotificationChannel, NotificationType, NotificationPriority,
    UserNotificationPreference
)
from app.models.user import User
from app.exceptions.notification_exceptions import NotificationError
from app.services.email_service import EmailService
from app.services.sms_service import SMSService
from app.services.push_service import PushService
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class NotificationStrategy(str, Enum):
    """Notification delivery strategies."""
    ALL_CHANNELS = "all_channels"
    PREFERRED_CHANNEL = "preferred_channel"
    FALLBACK_CHANNELS = "fallback_channels"
    SMART_ROUTING = "smart_routing"


class NotificationService:
    """Main service for managing notifications across all channels."""
    
    def __init__(self, settings: Settings):
        """Initialize the notification service."""
        self.settings = settings
        self.audit_logger = AuditLogger()
        
        # Initialize channel services
        self.email_service = EmailService(settings)
        self.sms_service = SMSService(settings)
        self.push_service = PushService(settings)
        
        logger.info("Notification service initialized with all channels")
    
    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        strategy: NotificationStrategy = NotificationStrategy.SMART_ROUTING,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        scheduled_time: Optional[datetime] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Send a notification to a user.
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            channels: Specific channels to use (optional)
            strategy: Delivery strategy
            template_id: Template ID to use
            template_data: Data for template rendering
            scheduled_time: When to send (optional, for scheduling)
            db: Database session
            
        Returns:
            Dictionary with delivery results
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotificationError(f"User not found: {user_id}")
            
            # Determine channels to use
            if channels:
                target_channels = channels
            else:
                target_channels = self._determine_channels(user, notification_type, priority, strategy)
            
            # Create notification record
            notification = Notification(
                user_id=user_id,
                type=notification_type,
                title=title,
                message=message,
                priority=priority,
                channel=target_channels[0] if target_channels else NotificationChannel.EMAIL,
                template_id=template_id,
                template_data=template_data,
                status=NotificationStatus.PENDING
            )
            
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send to each channel
            results = {}
            for channel in target_channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        result = await self.email_service.send_notification_email(notification, db)
                    elif channel == NotificationChannel.SMS:
                        result = await self.sms_service.send_notification_sms(notification, db)
                    elif channel == NotificationChannel.PUSH:
                        result = await self.push_service.send_notification_push(notification, db)
                    else:
                        logger.warning(f"Unsupported channel: {channel}")
                        continue
                    
                    results[channel.value] = result
                    
                    # If successful and using preferred channel strategy, stop
                    if strategy == NotificationStrategy.PREFERRED_CHANNEL and result.get("success"):
                        break
                        
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel}: {e}")
                    results[channel.value] = {
                        "success": False,
                        "error": str(e)
                    }
                    
                    # Continue with other channels if using fallback strategy
                    if strategy == NotificationStrategy.FALLBACK_CHANNELS:
                        continue
                    else:
                        break
            
            # Log notification sent
            self.audit_logger.log_system_action(
                action="notification_sent",
                details={
                    "user_id": user_id,
                    "notification_id": notification.id,
                    "type": notification_type.value,
                    "priority": priority.value,
                    "channels": [c.value for c in target_channels],
                    "strategy": strategy.value,
                    "results": results
                }
            )
            
            return {
                "notification_id": notification.id,
                "user_id": user_id,
                "channels_attempted": [c.value for c in target_channels],
                "results": results,
                "success": any(r.get("success", False) for r in results.values())
            }
            
        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            raise NotificationError(f"Failed to send notification: {e}")
    
    def _determine_channels(
        self,
        user: User,
        notification_type: NotificationType,
        priority: NotificationPriority,
        strategy: NotificationStrategy
    ) -> List[NotificationChannel]:
        """
        Determine which channels to use for notification delivery.
        
        Args:
            user: Target user
            notification_type: Type of notification
            priority: Notification priority
            strategy: Delivery strategy
            
        Returns:
            List of channels to use
        """
        channels = []
        
        # Get user preferences
        prefs = user.notification_preferences
        
        if strategy == NotificationStrategy.ALL_CHANNELS:
            # Send to all enabled channels
            if prefs:
                if prefs.email_enabled:
                    channels.append(NotificationChannel.EMAIL)
                if prefs.sms_enabled:
                    channels.append(NotificationChannel.SMS)
                if prefs.push_enabled:
                    channels.append(NotificationChannel.PUSH)
            else:
                # Default to email if no preferences
                channels.append(NotificationChannel.EMAIL)
        
        elif strategy == NotificationStrategy.PREFERRED_CHANNEL:
            # Use user's preferred channel for this notification type
            if prefs and prefs.preferences:
                type_prefs = prefs.preferences.get(notification_type.value, {})
                preferred_channel = type_prefs.get("preferred_channel")
                
                if preferred_channel == "email" and prefs.email_enabled:
                    channels.append(NotificationChannel.EMAIL)
                elif preferred_channel == "sms" and prefs.sms_enabled:
                    channels.append(NotificationChannel.SMS)
                elif preferred_channel == "push" and prefs.push_enabled:
                    channels.append(NotificationChannel.PUSH)
                else:
                    # Fallback to email
                    channels.append(NotificationChannel.EMAIL)
            else:
                channels.append(NotificationChannel.EMAIL)
        
        elif strategy == NotificationStrategy.FALLBACK_CHANNELS:
            # Try channels in order of preference, with fallbacks
            if prefs:
                if prefs.email_enabled:
                    channels.append(NotificationChannel.EMAIL)
                if prefs.sms_enabled:
                    channels.append(NotificationChannel.SMS)
                if prefs.push_enabled:
                    channels.append(NotificationChannel.PUSH)
            else:
                channels = [NotificationChannel.EMAIL, NotificationChannel.SMS, NotificationChannel.PUSH]
        
        elif strategy == NotificationStrategy.SMART_ROUTING:
            # Smart routing based on notification type, priority, and user preferences
            channels = self._smart_route_notification(user, notification_type, priority)
        
        # Ensure at least one channel is selected
        if not channels:
            channels.append(NotificationChannel.EMAIL)
        
        return channels
    
    def _smart_route_notification(
        self,
        user: User,
        notification_type: NotificationType,
        priority: NotificationPriority
    ) -> List[NotificationChannel]:
        """
        Smart routing based on notification type and priority.
        
        Args:
            user: Target user
            notification_type: Type of notification
            priority: Notification priority
            
        Returns:
            List of channels in order of preference
        """
        channels = []
        prefs = user.notification_preferences
        
        # Emergency alerts: All channels immediately
        if priority == NotificationPriority.EMERGENCY:
            if prefs and prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)  # SMS first for emergencies
            if prefs and prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            return channels
        
        # Urgent notifications: SMS + Push
        elif priority == NotificationPriority.URGENT:
            if prefs and prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if prefs and prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            return channels
        
        # High priority: Push + Email
        elif priority == NotificationPriority.HIGH:
            if prefs and prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if prefs and prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            return channels
        
        # Type-specific routing
        elif notification_type == NotificationType.MEDICATION_REMINDER:
            # Medication reminders: SMS preferred (immediate attention)
            if prefs and prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if prefs and prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
        
        elif notification_type == NotificationType.APPOINTMENT_REMINDER:
            # Appointment reminders: Email + Push
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if prefs and prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs and prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
        
        elif notification_type in [NotificationType.WEEKLY_SUMMARY, NotificationType.MONTHLY_REPORT]:
            # Reports: Email only (detailed content)
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
        
        else:
            # Default: Push + Email
            if prefs and prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs and prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if prefs and prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
        
        return channels
    
    async def send_bulk_notifications(
        self,
        user_ids: List[int],
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        channels: Optional[List[NotificationChannel]] = None,
        strategy: NotificationStrategy = NotificationStrategy.SMART_ROUTING,
        template_id: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Send notifications to multiple users.
        
        Args:
            user_ids: List of target user IDs
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            channels: Specific channels to use
            strategy: Delivery strategy
            template_id: Template ID to use
            template_data: Data for template rendering
            db: Database session
            
        Returns:
            Dictionary with bulk delivery results
        """
        results = {
            "total_users": len(user_ids),
            "successful": 0,
            "failed": 0,
            "user_results": {}
        }
        
        for user_id in user_ids:
            try:
                result = await self.send_notification(
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    channels=channels,
                    strategy=strategy,
                    template_id=template_id,
                    template_data=template_data,
                    db=db
                )
                
                results["user_results"][user_id] = result
                if result.get("success"):
                    results["successful"] += 1
                else:
                    results["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Failed to send bulk notification to user {user_id}: {e}")
                results["user_results"][user_id] = {
                    "success": False,
                    "error": str(e)
                }
                results["failed"] += 1
        
        return results
    
    async def get_notification_status(
        self,
        notification_id: int,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get the status of a notification.
        
        Args:
            notification_id: Notification ID
            db: Database session
            
        Returns:
            Notification status information
        """
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if not notification:
                raise NotificationError(f"Notification not found: {notification_id}")
            
            # Get delivery attempts
            delivery_attempts = db.query(NotificationDeliveryAttempt).filter(
                NotificationDeliveryAttempt.notification_id == notification_id
            ).all()
            
            return {
                "notification": notification.to_dict(include_sensitive=True),
                "delivery_attempts": [attempt.to_dict(include_sensitive=True) for attempt in delivery_attempts],
                "status_summary": {
                    "total_attempts": len(delivery_attempts),
                    "successful_attempts": len([a for a in delivery_attempts if a.status == NotificationStatus.SENT]),
                    "failed_attempts": len([a for a in delivery_attempts if a.status == NotificationStatus.FAILED]),
                    "delivered_attempts": len([a for a in delivery_attempts if a.status == NotificationStatus.DELIVERED])
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification status for {notification_id}: {e}")
            raise NotificationError(f"Failed to get notification status: {e}")
    
    async def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50,
        offset: int = 0,
        status: Optional[NotificationStatus] = None,
        notification_type: Optional[NotificationType] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get notifications for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            status: Filter by status
            notification_type: Filter by type
            db: Database session
            
        Returns:
            User notifications
        """
        try:
            query = db.query(Notification).filter(Notification.user_id == user_id)
            
            if status:
                query = query.filter(Notification.status == status)
            
            if notification_type:
                query = query.filter(Notification.type == notification_type)
            
            total_count = query.count()
            notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
            
            return {
                "notifications": [n.to_dict() for n in notifications],
                "total_count": total_count,
                "limit": limit,
                "offset": offset
            }
            
        except Exception as e:
            logger.error(f"Failed to get notifications for user {user_id}: {e}")
            raise NotificationError(f"Failed to get user notifications: {e}")
    
    async def update_notification_preferences(
        self,
        user_id: int,
        preferences: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        Update user notification preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences
            db: Database session
            
        Returns:
            True if successful, False otherwise
        """
        try:
            prefs = db.query(UserNotificationPreference).filter(
                UserNotificationPreference.user_id == user_id
            ).first()
            
            if not prefs:
                prefs = UserNotificationPreference(user_id=user_id)
                db.add(prefs)
            
            # Update preferences
            for key, value in preferences.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            db.commit()
            logger.info(f"Updated notification preferences for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update notification preferences for user {user_id}: {e}")
            return False
    
    async def get_notification_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[int] = None,
        notification_type: Optional[NotificationType] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Get notification analytics.
        
        Args:
            start_date: Start date for analytics
            end_date: End date for analytics
            user_id: Optional user ID to filter by
            notification_type: Optional notification type to filter by
            db: Database session
            
        Returns:
            Analytics data
        """
        try:
            query = db.query(Notification)
            
            if start_date:
                query = query.filter(Notification.created_at >= start_date)
            
            if end_date:
                query = query.filter(Notification.created_at <= end_date)
            
            if user_id:
                query = query.filter(Notification.user_id == user_id)
            
            if notification_type:
                query = query.filter(Notification.type == notification_type)
            
            notifications = query.all()
            
            # Calculate analytics
            total_notifications = len(notifications)
            status_counts = {}
            channel_counts = {}
            type_counts = {}
            priority_counts = {}
            
            for notification in notifications:
                # Status counts
                status = notification.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Channel counts
                channel = notification.channel.value
                channel_counts[channel] = channel_counts.get(channel, 0) + 1
                
                # Type counts
                ntype = notification.type.value
                type_counts[ntype] = type_counts.get(ntype, 0) + 1
                
                # Priority counts
                priority = notification.priority.value
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            return {
                "total_notifications": total_notifications,
                "status_breakdown": status_counts,
                "channel_breakdown": channel_counts,
                "type_breakdown": type_counts,
                "priority_breakdown": priority_counts,
                "delivery_rate": (status_counts.get("sent", 0) + status_counts.get("delivered", 0)) / total_notifications if total_notifications > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get notification analytics: {e}")
            raise NotificationError(f"Failed to get notification analytics: {e}") 