"""
Real-time Notification WebSocket Delivery System.

This module provides WebSocket handlers for real-time notification delivery,
including health alerts, medication reminders, and system notifications.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.websocket.connection_manager import connection_manager
from app.websocket.auth import WebSocketAuth
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Types of notifications that can be sent."""
    HEALTH_ALERT = "health_alert"
    MEDICATION_REMINDER = "medication_reminder"
    APPOINTMENT_REMINDER = "appointment_reminder"
    SYSTEM_NOTIFICATION = "system_notification"
    CHAT_MESSAGE = "chat_message"
    GOAL_ACHIEVEMENT = "goal_achievement"
    EMERGENCY_ALERT = "emergency_alert"

class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    EMERGENCY = "emergency"

class NotificationWebSocket:
    """WebSocket handler for real-time notification delivery."""
    
    def __init__(self):
        """Initialize the notification WebSocket handler."""
        self.audit_logger = AuditLogger()
        self.notification_queue: Dict[str, List[Dict[str, Any]]] = {}
        self.user_preferences: Dict[int, Dict[str, Any]] = {}
    
    async def handle_websocket(self, websocket: WebSocket, db: Session):
        """
        Handle WebSocket connection for notification delivery.
        
        Args:
            websocket: WebSocket connection
            db: Database session
        """
        connection_id = None
        try:
            # Accept connection
            connection_id = await connection_manager.connect(websocket)
            
            # Wait for authentication
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Validate message format
            if not WebSocketAuth.validate_message_format(message):
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid message format",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # Handle authentication
            if message.get("type") == "authenticate":
                user = await WebSocketAuth.handle_authentication_message(
                    websocket, message, db
                )
                
                # Create notification subscription
                subscription = WebSocketAuth.create_notification_subscription(user.id)
                await connection_manager.subscribe(connection_id, subscription)
                
                await websocket.send_text(json.dumps({
                    "type": "authenticated",
                    "message": "Successfully authenticated for notifications",
                    "user_id": user.id,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                
                # Send any pending notifications
                await self._send_pending_notifications(websocket, user.id)
                
            # Handle subscription management
            elif message.get("type") == "subscribe":
                success = await WebSocketAuth.handle_subscription_message(
                    websocket, message, user
                )
                if success:
                    await websocket.send_text(json.dumps({
                        "type": "subscribed",
                        "message": "Successfully subscribed to notifications",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Failed to subscribe to notifications",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
            
            # Handle notification preferences
            elif message.get("type") == "update_preferences":
                await self._handle_update_preferences(websocket, user, message)
            
            # Handle notification acknowledgment
            elif message.get("type") == "acknowledge":
                await self._handle_acknowledge_notification(websocket, user, message, db)
            
            # Handle notification dismissal
            elif message.get("type") == "dismiss":
                await self._handle_dismiss_notification(websocket, user, message, db)
            
            # Handle get notification history
            elif message.get("type") == "get_history":
                await self._handle_get_notification_history(websocket, user, message, db)
            
            # Handle mark as read
            elif message.get("type") == "mark_read":
                await self._handle_mark_as_read(websocket, user, message, db)
            
            else:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Unknown message type",
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            # Keep connection alive and handle incoming messages
            while True:
                try:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Handle different message types
                    if message.get("type") == "ping":
                        await websocket.send_text(json.dumps({
                            "type": "pong",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                    
                    elif message.get("type") == "update_preferences":
                        await self._handle_update_preferences(websocket, user, message)
                    
                    elif message.get("type") == "acknowledge":
                        await self._handle_acknowledge_notification(websocket, user, message, db)
                    
                    elif message.get("type") == "dismiss":
                        await self._handle_dismiss_notification(websocket, user, message, db)
                    
                    else:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Unknown message type",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                
                except WebSocketDisconnect:
                    break
                    
        except WebSocketDisconnect:
            logger.info(f"Notification WebSocket disconnected: {connection_id}")
        except Exception as e:
            logger.error(f"Notification WebSocket error: {e}")
            if connection_id:
                await connection_manager.disconnect(connection_id, f"Error: {str(e)}")
    
    async def _handle_update_preferences(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any]
    ):
        """
        Handle notification preference updates.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Message containing preference updates
        """
        try:
            preferences = message.get("preferences", {})
            
            # Validate preferences
            valid_types = [nt.value for nt in NotificationType]
            valid_priorities = [np.value for np in NotificationPriority]
            
            for notification_type, settings in preferences.items():
                if notification_type not in valid_types:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Invalid notification type: {notification_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    return
                
                if "priority" in settings and settings["priority"] not in valid_priorities:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Invalid priority: {settings['priority']}",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    return
            
            # Update user preferences
            self.user_preferences[user.id] = preferences
            
            await websocket.send_text(json.dumps({
                "type": "preferences_updated",
                "message": "Notification preferences updated successfully",
                "preferences": preferences,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Log preference update
            self.audit_logger.log_user_action(
                user_id=user.id,
                action="update_notification_preferences",
                details={"preferences": preferences}
            )
            
        except Exception as e:
            logger.error(f"Error updating notification preferences: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to update notification preferences",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_acknowledge_notification(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle notification acknowledgment.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Message containing notification ID
            db: Database session
        """
        try:
            notification_id = message.get("notification_id")
            if not notification_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Missing notification ID",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # TODO: Update notification status in database
            # This would typically update a notification record to mark it as acknowledged
            
            await websocket.send_text(json.dumps({
                "type": "acknowledged",
                "message": "Notification acknowledged",
                "notification_id": notification_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Log acknowledgment
            self.audit_logger.log_user_action(
                user_id=user.id,
                action="acknowledge_notification",
                details={"notification_id": notification_id}
            )
            
        except Exception as e:
            logger.error(f"Error acknowledging notification: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to acknowledge notification",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_dismiss_notification(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle notification dismissal.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Message containing notification ID
            db: Database session
        """
        try:
            notification_id = message.get("notification_id")
            if not notification_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Missing notification ID",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # TODO: Update notification status in database
            # This would typically update a notification record to mark it as dismissed
            
            await websocket.send_text(json.dumps({
                "type": "dismissed",
                "message": "Notification dismissed",
                "notification_id": notification_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Log dismissal
            self.audit_logger.log_user_action(
                user_id=user.id,
                action="dismiss_notification",
                details={"notification_id": notification_id}
            )
            
        except Exception as e:
            logger.error(f"Error dismissing notification: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to dismiss notification",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_get_notification_history(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle notification history request.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Message containing query parameters
            db: Database session
        """
        try:
            limit = message.get("limit", 50)
            offset = message.get("offset", 0)
            notification_type = message.get("type")
            read_status = message.get("read_status")
            
            # TODO: Query notification history from database
            # This would typically query a notifications table
            
            # Mock response for now
            notifications = [
                {
                    "id": "1",
                    "type": NotificationType.HEALTH_ALERT.value,
                    "title": "Blood pressure alert",
                    "message": "Your blood pressure reading is above normal range",
                    "priority": NotificationPriority.HIGH.value,
                    "created_at": datetime.utcnow().isoformat(),
                    "read": False,
                    "acknowledged": False
                }
            ]
            
            await websocket.send_text(json.dumps({
                "type": "notification_history",
                "notifications": notifications,
                "total": len(notifications),
                "limit": limit,
                "offset": offset,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
        except Exception as e:
            logger.error(f"Error getting notification history: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to get notification history",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_mark_as_read(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle mark notifications as read.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Message containing notification IDs
            db: Database session
        """
        try:
            notification_ids = message.get("notification_ids", [])
            if not notification_ids:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Missing notification IDs",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # TODO: Update notification status in database
            # This would typically update notification records to mark them as read
            
            await websocket.send_text(json.dumps({
                "type": "marked_read",
                "message": f"Marked {len(notification_ids)} notifications as read",
                "notification_ids": notification_ids,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Log action
            self.audit_logger.log_user_action(
                user_id=user.id,
                action="mark_notifications_read",
                details={"notification_ids": notification_ids}
            )
            
        except Exception as e:
            logger.error(f"Error marking notifications as read: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to mark notifications as read",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _send_pending_notifications(self, websocket: WebSocket, user_id: int):
        """
        Send any pending notifications for the user.
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        try:
            # Check for pending notifications in queue
            if user_id in self.notification_queue:
                pending_notifications = self.notification_queue[user_id]
                
                for notification in pending_notifications:
                    await websocket.send_text(json.dumps({
                        "type": "notification",
                        "notification": notification,
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                # Clear the queue after sending
                self.notification_queue[user_id] = []
                
        except Exception as e:
            logger.error(f"Error sending pending notifications: {e}")
    
    async def send_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Send a notification to a specific user.
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority
            metadata: Additional notification metadata
        """
        try:
            notification = {
                "id": str(len(self.notification_queue.get(user_id, [])) + 1),
                "type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "created_at": datetime.utcnow().isoformat(),
                "read": False,
                "acknowledged": False,
                "metadata": metadata or {}
            }
            
            # Check user preferences
            user_prefs = self.user_preferences.get(user_id, {})
            notification_prefs = user_prefs.get(notification_type.value, {})
            
            # Check if user wants this type of notification
            if notification_prefs.get("enabled", True):
                # Check priority filter
                min_priority = notification_prefs.get("min_priority", NotificationPriority.LOW.value)
                if self._is_priority_higher_or_equal(priority.value, min_priority):
                    # Try to send immediately if user is connected
                    success = await connection_manager.send_to_user(user_id, {
                        "type": "notification",
                        "notification": notification,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    if not success:
                        # Queue for later if user is not connected
                        if user_id not in self.notification_queue:
                            self.notification_queue[user_id] = []
                        self.notification_queue[user_id].append(notification)
                        
                        # Limit queue size
                        if len(self.notification_queue[user_id]) > 100:
                            self.notification_queue[user_id] = self.notification_queue[user_id][-50:]
            
            # Log notification
            self.audit_logger.log_system_action(
                action="send_notification",
                details={
                    "user_id": user_id,
                    "notification_type": notification_type.value,
                    "priority": priority.value,
                    "title": title
                }
            )
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def _is_priority_higher_or_equal(self, priority: str, min_priority: str) -> bool:
        """
        Check if a priority is higher or equal to minimum priority.
        
        Args:
            priority: Current priority
            min_priority: Minimum required priority
            
        Returns:
            True if priority is higher or equal
        """
        priority_order = {
            NotificationPriority.LOW.value: 1,
            NotificationPriority.NORMAL.value: 2,
            NotificationPriority.HIGH.value: 3,
            NotificationPriority.URGENT.value: 4,
            NotificationPriority.EMERGENCY.value: 5
        }
        
        return priority_order.get(priority, 0) >= priority_order.get(min_priority, 0)

# Global notification WebSocket handler instance
notification_websocket = NotificationWebSocket() 