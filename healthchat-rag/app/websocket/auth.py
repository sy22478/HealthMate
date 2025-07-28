"""
WebSocket Authentication and Authorization.

This module provides authentication and authorization utilities for WebSocket connections.
It handles token validation, user verification, and permission checking.
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)

class WebSocketAuth:
    """WebSocket authentication and authorization utilities."""
    
    @staticmethod
    async def authenticate_websocket(
        websocket: WebSocket,
        token: str,
        db: Session
    ) -> Optional[User]:
        """
        Authenticate a WebSocket connection using JWT token.
        
        Args:
            websocket: WebSocket connection
            token: JWT token
            db: Database session
            
        Returns:
            Authenticated user or None
        """
        try:
            # Validate token
            auth_service = AuthService(db)
            user_id = auth_service.get_user_id_from_token(token)
            
            if not user_id:
                await websocket.send_text(json.dumps({
                    "type": "authentication_failed",
                    "message": "Invalid token",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return None
            
            # Get user info
            user = auth_service.get_user_by_id(user_id)
            if not user:
                await websocket.send_text(json.dumps({
                    "type": "authentication_failed",
                    "message": "User not found",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return None
            
            # Check if user is active
            if not user.is_active:
                await websocket.send_text(json.dumps({
                    "type": "authentication_failed",
                    "message": "User account is inactive",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return None
            
            # Send authentication success
            await websocket.send_text(json.dumps({
                "type": "authentication_success",
                "user_id": user.id,
                "user_email": user.email,
                "user_role": user.role,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Authentication successful"
            }))
            
            # Audit log
            AuditLogger.log_auth_event(
                event_type="websocket_authentication",
                user_id=user.id,
                user_email=user.email,
                success=True,
                details={"connection_type": "websocket"}
            )
            
            logger.info(f"WebSocket authenticated for user {user.id} ({user.email})")
            return user
            
        except Exception as e:
            logger.error(f"WebSocket authentication error: {e}")
            await websocket.send_text(json.dumps({
                "type": "authentication_failed",
                "message": "Authentication error",
                "timestamp": datetime.utcnow().isoformat()
            }))
            return None
    
    @staticmethod
    def check_permission(user: User, resource: str, action: str) -> bool:
        """
        Check if user has permission for a specific resource and action.
        
        Args:
            user: Authenticated user
            resource: Resource to access
            action: Action to perform
            
        Returns:
            True if user has permission
        """
        # Admin users have all permissions
        if user.role == "admin":
            return True
        
        # Define permission matrix
        permissions = {
            "user": {
                "health_data": ["read", "write", "delete"],
                "chat": ["read", "write"],
                "notifications": ["read"],
                "profile": ["read", "write"]
            },
            "doctor": {
                "health_data": ["read"],
                "chat": ["read", "write"],
                "notifications": ["read", "write"],
                "patient_data": ["read"]
            },
            "nurse": {
                "health_data": ["read"],
                "chat": ["read", "write"],
                "notifications": ["read"],
                "patient_data": ["read"]
            }
        }
        
        # Check user permissions
        user_permissions = permissions.get(user.role, {})
        resource_permissions = user_permissions.get(resource, [])
        
        return action in resource_permissions
    
    @staticmethod
    async def authorize_subscription(
        user: User,
        subscription: str,
        websocket: WebSocket
    ) -> bool:
        """
        Authorize user subscription to a specific topic.
        
        Args:
            user: Authenticated user
            subscription: Subscription topic
            websocket: WebSocket connection
            
        Returns:
            True if subscription is authorized
        """
        try:
            # Parse subscription format: topic:resource:action
            parts = subscription.split(":")
            if len(parts) < 2:
                await websocket.send_text(json.dumps({
                    "type": "subscription_denied",
                    "subscription": subscription,
                    "message": "Invalid subscription format",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return False
            
            topic = parts[0]
            resource = parts[1] if len(parts) > 1 else topic
            action = parts[2] if len(parts) > 2 else "read"
            
            # Check permissions
            if not WebSocketAuth.check_permission(user, resource, action):
                await websocket.send_text(json.dumps({
                    "type": "subscription_denied",
                    "subscription": subscription,
                    "message": "Insufficient permissions",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return False
            
            # Special handling for user-specific subscriptions
            if topic == "user" and not subscription.endswith(f":{user.id}"):
                await websocket.send_text(json.dumps({
                    "type": "subscription_denied",
                    "subscription": subscription,
                    "message": "Can only subscribe to own user data",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return False
            
            # Audit log
            AuditLogger.log_auth_event(
                event_type="websocket_subscription",
                user_id=user.id,
                user_email=user.email,
                success=True,
                details={
                    "subscription": subscription,
                    "topic": topic,
                    "resource": resource,
                    "action": action
                }
            )
            
            logger.info(f"Subscription authorized: {user.id} -> {subscription}")
            return True
            
        except Exception as e:
            logger.error(f"Subscription authorization error: {e}")
            await websocket.send_text(json.dumps({
                "type": "subscription_denied",
                "subscription": subscription,
                "message": "Authorization error",
                "timestamp": datetime.utcnow().isoformat()
            }))
            return False
    
    @staticmethod
    def validate_message_format(message: Dict[str, Any]) -> bool:
        """
        Validate WebSocket message format.
        
        Args:
            message: Message to validate
            
        Returns:
            True if message format is valid
        """
        required_fields = ["type"]
        
        # Check required fields
        for field in required_fields:
            if field not in message:
                return False
        
        # Validate message types
        valid_types = [
            "authentication",
            "subscribe",
            "unsubscribe",
            "message",
            "ping",
            "pong"
        ]
        
        if message["type"] not in valid_types:
            return False
        
        return True
    
    @staticmethod
    async def handle_authentication_message(
        websocket: WebSocket,
        message: Dict[str, Any],
        db: Session
    ) -> Optional[User]:
        """
        Handle authentication message from WebSocket.
        
        Args:
            websocket: WebSocket connection
            message: Authentication message
            db: Database session
            
        Returns:
            Authenticated user or None
        """
        try:
            token = message.get("token")
            if not token:
                await websocket.send_text(json.dumps({
                    "type": "authentication_failed",
                    "message": "Token required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return None
            
            return await WebSocketAuth.authenticate_websocket(websocket, token, db)
            
        except Exception as e:
            logger.error(f"Authentication message handling error: {e}")
            await websocket.send_text(json.dumps({
                "type": "authentication_failed",
                "message": "Authentication error",
                "timestamp": datetime.utcnow().isoformat()
            }))
            return None
    
    @staticmethod
    async def handle_subscription_message(
        websocket: WebSocket,
        message: Dict[str, Any],
        user: User
    ) -> bool:
        """
        Handle subscription message from WebSocket.
        
        Args:
            websocket: WebSocket connection
            message: Subscription message
            user: Authenticated user
            
        Returns:
            True if subscription successful
        """
        try:
            subscription = message.get("subscription")
            if not subscription:
                await websocket.send_text(json.dumps({
                    "type": "subscription_failed",
                    "message": "Subscription topic required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return False
            
            return await WebSocketAuth.authorize_subscription(user, subscription, websocket)
            
        except Exception as e:
            logger.error(f"Subscription message handling error: {e}")
            await websocket.send_text(json.dumps({
                "type": "subscription_failed",
                "message": "Subscription error",
                "timestamp": datetime.utcnow().isoformat()
            }))
            return False
    
    @staticmethod
    def create_user_subscription(user_id: int, topic: str) -> str:
        """
        Create a user-specific subscription topic.
        
        Args:
            user_id: User ID
            topic: Topic name
            
        Returns:
            Subscription topic string
        """
        return f"user:{topic}:{user_id}"
    
    @staticmethod
    def create_health_data_subscription(user_id: int, data_type: str = None) -> str:
        """
        Create a health data subscription topic.
        
        Args:
            user_id: User ID
            data_type: Specific data type (optional)
            
        Returns:
            Subscription topic string
        """
        if data_type:
            return f"health_data:{data_type}:{user_id}"
        return f"health_data:all:{user_id}"
    
    @staticmethod
    def create_chat_subscription(user_id: int, conversation_id: str = None) -> str:
        """
        Create a chat subscription topic.
        
        Args:
            user_id: User ID
            conversation_id: Specific conversation ID (optional)
            
        Returns:
            Subscription topic string
        """
        if conversation_id:
            return f"chat:conversation:{conversation_id}:{user_id}"
        return f"chat:user:{user_id}"
    
    @staticmethod
    def create_notification_subscription(user_id: int, notification_type: str = None) -> str:
        """
        Create a notification subscription topic.
        
        Args:
            user_id: User ID
            notification_type: Specific notification type (optional)
            
        Returns:
            Subscription topic string
        """
        if notification_type:
            return f"notifications:{notification_type}:{user_id}"
        return f"notifications:all:{user_id}" 