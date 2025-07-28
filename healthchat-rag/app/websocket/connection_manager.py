"""
WebSocket Connection Manager.

This module provides connection management, pooling, and scaling for WebSocket connections.
It handles connection lifecycle, authentication, and message routing.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Set, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth import AuthService
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    connection_id: str
    websocket: WebSocket
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    state: ConnectionState = ConnectionState.CONNECTING
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    last_error: Optional[str] = None
    recovery_attempts: int = 0

class ConnectionManager:
    """Manages WebSocket connections with pooling and scaling capabilities."""
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, ConnectionInfo] = {}
        self.user_connections: Dict[int, Set[str]] = {}
        self.subscription_connections: Dict[str, Set[str]] = {}
        self.connection_pool: List[ConnectionInfo] = []
        self.max_connections: int = 1000
        self.max_connections_per_user: int = 5
        self.connection_timeout: int = 3600  # 1 hour
        self.heartbeat_interval: int = 30  # 30 seconds
        self.cleanup_interval: int = 300  # 5 minutes
        self.recovery_interval: int = 60  # 1 minute
        self.max_recovery_attempts: int = 5
        
        # Background tasks will be started when first connection is made
        self._background_tasks_started = False
    
    async def connect(self, websocket: WebSocket) -> str:
        """
        Accept a new WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            
        Returns:
            Connection ID
        """
        # Start background tasks if not already started
        if not self._background_tasks_started:
            asyncio.create_task(self._heartbeat_task())
            asyncio.create_task(self._cleanup_task())
            asyncio.create_task(self._recovery_task())
            self._background_tasks_started = True
        
        await websocket.accept()
        
        # Check connection limits
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Server overloaded")
            raise WebSocketDisconnect()
        
        # Create connection info
        connection_id = str(uuid.uuid4())
        connection_info = ConnectionInfo(
            connection_id=connection_id,
            websocket=websocket,
            state=ConnectionState.CONNECTED
        )
        
        # Store connection
        self.active_connections[connection_id] = connection_info
        
        logger.info(f"WebSocket connected: {connection_id}")
        
        # Send welcome message
        await self._send_to_connection(connection_id, {
            "type": "connection_established",
            "connection_id": connection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "WebSocket connection established"
        })
        
        return connection_id
    
    async def authenticate_connection(
        self,
        connection_id: str,
        token: str,
        db: Session
    ) -> bool:
        """
        Authenticate a WebSocket connection using JWT token.
        
        Args:
            connection_id: Connection ID
            token: JWT token
            db: Database session
            
        Returns:
            True if authentication successful
        """
        try:
            # Get connection info
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return False
            
            # Validate token
            auth_service = AuthService(db)
            user_id = auth_service.get_user_id_from_token(token)
            
            if not user_id:
                await self._send_to_connection(connection_id, {
                    "type": "authentication_failed",
                    "message": "Invalid token"
                })
                return False
            
            # Get user info
            user = auth_service.get_user_by_id(user_id)
            if not user:
                await self._send_to_connection(connection_id, {
                    "type": "authentication_failed",
                    "message": "User not found"
                })
                return False
            
            # Check connection limits per user
            user_connections = self.user_connections.get(user_id, set())
            if len(user_connections) >= self.max_connections_per_user:
                await self._send_to_connection(connection_id, {
                    "type": "authentication_failed",
                    "message": "Too many connections for user"
                })
                return False
            
            # Update connection info
            connection_info.user_id = user_id
            connection_info.user_email = user.email
            connection_info.state = ConnectionState.AUTHENTICATED
            connection_info.last_activity = datetime.utcnow()
            
            # Add to user connections
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection_id)
            
            # Send authentication success
            await self._send_to_connection(connection_id, {
                "type": "authentication_success",
                "user_id": user_id,
                "user_email": user.email,
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Authentication successful"
            })
            
            # Audit log
            AuditLogger.log_auth_event(
                event_type="websocket_authentication",
                user_id=user_id,
                user_email=user.email,
                success=True,
                details={"connection_id": connection_id}
            )
            
            logger.info(f"WebSocket authenticated: {connection_id} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self._send_to_connection(connection_id, {
                "type": "authentication_failed",
                "message": "Authentication error"
            })
            return False
    
    async def disconnect(self, connection_id: str, reason: str = "Normal disconnect"):
        """
        Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection ID
            reason: Disconnect reason
        """
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return
            
            # Remove from subscriptions
            for subscription in connection_info.subscriptions:
                if subscription in self.subscription_connections:
                    self.subscription_connections[subscription].discard(connection_id)
            
            # Remove from user connections
            if connection_info.user_id:
                user_connections = self.user_connections.get(connection_info.user_id, set())
                user_connections.discard(connection_id)
                if not user_connections:
                    del self.user_connections[connection_info.user_id]
            
            # Close WebSocket
            await connection_info.websocket.close(code=1000, reason=reason)
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Audit log
            if connection_info.user_id:
                AuditLogger.log_auth_event(
                    event_type="websocket_disconnect",
                    user_id=connection_info.user_id,
                    user_email=connection_info.user_email,
                    success=True,
                    details={"connection_id": connection_id, "reason": reason}
                )
            
            logger.info(f"WebSocket disconnected: {connection_id} - {reason}")
            
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
    
    async def subscribe(self, connection_id: str, subscription: str) -> bool:
        """
        Subscribe a connection to a topic.
        
        Args:
            connection_id: Connection ID
            subscription: Subscription topic
            
        Returns:
            True if subscription successful
        """
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info or connection_info.state != ConnectionState.AUTHENTICATED:
                return False
            
            # Add to connection subscriptions
            connection_info.subscriptions.add(subscription)
            
            # Add to topic subscriptions
            if subscription not in self.subscription_connections:
                self.subscription_connections[subscription] = set()
            self.subscription_connections[subscription].add(connection_id)
            
            # Send subscription confirmation
            await self._send_to_connection(connection_id, {
                "type": "subscription_success",
                "subscription": subscription,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Subscription added: {connection_id} -> {subscription}")
            return True
            
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            return False
    
    async def unsubscribe(self, connection_id: str, subscription: str) -> bool:
        """
        Unsubscribe a connection from a topic.
        
        Args:
            connection_id: Connection ID
            subscription: Subscription topic
            
        Returns:
            True if unsubscription successful
        """
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return False
            
            # Remove from connection subscriptions
            connection_info.subscriptions.discard(subscription)
            
            # Remove from topic subscriptions
            if subscription in self.subscription_connections:
                self.subscription_connections[subscription].discard(connection_id)
                if not self.subscription_connections[subscription]:
                    del self.subscription_connections[subscription]
            
            # Send unsubscription confirmation
            await self._send_to_connection(connection_id, {
                "type": "unsubscription_success",
                "subscription": subscription,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info(f"Subscription removed: {connection_id} -> {subscription}")
            return True
            
        except Exception as e:
            logger.error(f"Unsubscription error: {e}")
            return False
    
    async def broadcast(self, message: Dict[str, Any], subscription: str = None):
        """
        Broadcast a message to all connections or a specific subscription.
        
        Args:
            message: Message to broadcast
            subscription: Optional subscription topic
        """
        try:
            if subscription:
                # Broadcast to subscription
                connection_ids = self.subscription_connections.get(subscription, set())
            else:
                # Broadcast to all authenticated connections
                connection_ids = {
                    conn_id for conn_id, conn_info in self.active_connections.items()
                    if conn_info.state == ConnectionState.AUTHENTICATED
                }
            
            # Send message to all connections
            tasks = []
            for connection_id in connection_ids:
                tasks.append(self._send_to_connection(connection_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Broadcast sent to {len(connection_ids)} connections")
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """
        Send a message to all connections of a specific user.
        
        Args:
            user_id: User ID
            message: Message to send
        """
        try:
            connection_ids = self.user_connections.get(user_id, set())
            
            tasks = []
            for connection_id in connection_ids:
                tasks.append(self._send_to_connection(connection_id, message))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Message sent to user {user_id} on {len(connection_ids)} connections")
            
        except Exception as e:
            logger.error(f"Send to user error: {e}")
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]):
        """
        Send a message to a specific connection.
        
        Args:
            connection_id: Connection ID
            message: Message to send
        """
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return
            
            # Update last activity
            connection_info.last_activity = datetime.utcnow()
            
            # Send message
            await connection_info.websocket.send_text(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Send to connection error: {e}")
            # Mark connection for cleanup
            await self.disconnect(connection_id, "Send error")
    
    async def _heartbeat_task(self):
        """Send heartbeat messages to keep connections alive."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                heartbeat_message = {
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send heartbeat to all authenticated connections
                authenticated_connections = [
                    conn_id for conn_id, conn_info in self.active_connections.items()
                    if conn_info.state == ConnectionState.AUTHENTICATED
                ]
                
                for connection_id in authenticated_connections:
                    await self._send_to_connection(connection_id, heartbeat_message)
                
                logger.debug(f"Heartbeat sent to {len(authenticated_connections)} connections")
                
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
    
    async def _cleanup_task(self):
        """Clean up inactive connections."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                current_time = datetime.utcnow()
                inactive_connections = []
                
                for connection_id, connection_info in self.active_connections.items():
                    time_since_activity = (current_time - connection_info.last_activity).total_seconds()
                    
                    if time_since_activity > self.connection_timeout:
                        inactive_connections.append(connection_id)
                
                # Disconnect inactive connections
                for connection_id in inactive_connections:
                    await self.disconnect(connection_id, "Connection timeout")
                
                if inactive_connections:
                    logger.info(f"Cleaned up {len(inactive_connections)} inactive connections")
                
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics.
        
        Returns:
            Connection statistics
        """
        total_connections = len(self.active_connections)
        authenticated_connections = len([
            conn for conn in self.active_connections.values()
            if conn.state == ConnectionState.AUTHENTICATED
        ])
        
        total_subscriptions = len(self.subscription_connections)
        total_users = len(self.user_connections)
        
        return {
            "total_connections": total_connections,
            "authenticated_connections": authenticated_connections,
            "total_subscriptions": total_subscriptions,
            "total_users": total_users,
            "max_connections": self.max_connections,
            "max_connections_per_user": self.max_connections_per_user,
            "connection_timeout": self.connection_timeout,
            "heartbeat_interval": self.heartbeat_interval,
            "recovery_interval": self.recovery_interval,
            "max_recovery_attempts": self.max_recovery_attempts
        }
    
    async def _recovery_task(self):
        """Attempt to recover failed connections."""
        while True:
            try:
                await asyncio.sleep(self.recovery_interval)
                
                # Find connections that need recovery
                failed_connections = [
                    conn_id for conn_id, conn_info in self.active_connections.items()
                    if conn_info.state == ConnectionState.ERROR and 
                    conn_info.recovery_attempts < self.max_recovery_attempts
                ]
                
                for connection_id in failed_connections:
                    await self._attempt_connection_recovery(connection_id)
                
                if failed_connections:
                    logger.info(f"Recovery attempts for {len(failed_connections)} connections")
                
            except Exception as e:
                logger.error(f"Recovery task error: {e}")
    
    async def _attempt_connection_recovery(self, connection_id: str):
        """
        Attempt to recover a failed connection.
        
        Args:
            connection_id: Connection ID to recover
        """
        try:
            connection_info = self.active_connections.get(connection_id)
            if not connection_info:
                return
            
            # Increment recovery attempts
            connection_info.recovery_attempts += 1
            
            # Try to send a test message
            test_message = {
                "type": "recovery_test",
                "message": "Testing connection recovery",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_info.websocket.send_text(json.dumps(test_message))
            
            # If successful, mark as recovered
            connection_info.state = ConnectionState.CONNECTED
            connection_info.last_error = None
            connection_info.recovery_attempts = 0
            
            logger.info(f"Connection {connection_id} recovered successfully")
            
        except Exception as e:
            connection_info.last_error = str(e)
            logger.warning(f"Recovery attempt {connection_info.recovery_attempts} failed for {connection_id}: {e}")
            
            # If max attempts reached, disconnect
            if connection_info.recovery_attempts >= self.max_recovery_attempts:
                await self.disconnect(connection_id, f"Max recovery attempts reached: {e}")
    
    async def retry_send_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """
        Send a message with retry logic.
        
        Args:
            connection_id: Connection ID
            message: Message to send
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            True if message sent successfully, False otherwise
        """
        connection_info = self.active_connections.get(connection_id)
        if not connection_info:
            return False
        
        for attempt in range(max_retries + 1):
            try:
                await self._send_to_connection(connection_id, message)
                return True
                
            except Exception as e:
                connection_info.retry_count += 1
                connection_info.last_error = str(e)
                
                if attempt < max_retries:
                    logger.warning(f"Send attempt {attempt + 1} failed for {connection_id}: {e}")
                    await asyncio.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error(f"All send attempts failed for {connection_id}: {e}")
                    connection_info.state = ConnectionState.ERROR
                    return False
        
        return False
    
    async def reconnect_user(self, user_id: int) -> bool:
        """
        Attempt to reconnect a user's connections.
        
        Args:
            user_id: User ID to reconnect
            
        Returns:
            True if reconnection successful, False otherwise
        """
        try:
            user_connections = self.user_connections.get(user_id, set())
            reconnected = False
            
            for connection_id in list(user_connections):
                connection_info = self.active_connections.get(connection_id)
                if connection_info and connection_info.state == ConnectionState.ERROR:
                    if await self._attempt_connection_recovery(connection_id):
                        reconnected = True
            
            if reconnected:
                logger.info(f"Successfully reconnected user {user_id}")
            
            return reconnected
            
        except Exception as e:
            logger.error(f"Error reconnecting user {user_id}: {e}")
            return False
    
    def get_connection_health(self, connection_id: str) -> Dict[str, Any]:
        """
        Get health information for a specific connection.
        
        Args:
            connection_id: Connection ID
            
        Returns:
            Connection health information
        """
        connection_info = self.active_connections.get(connection_id)
        if not connection_info:
            return {"status": "not_found"}
        
        return {
            "connection_id": connection_id,
            "state": connection_info.state.value,
            "user_id": connection_info.user_id,
            "connected_at": connection_info.connected_at.isoformat(),
            "last_activity": connection_info.last_activity.isoformat(),
            "retry_count": connection_info.retry_count,
            "recovery_attempts": connection_info.recovery_attempts,
            "last_error": connection_info.last_error,
            "subscriptions": list(connection_info.subscriptions),
            "is_healthy": connection_info.state == ConnectionState.AUTHENTICATED
        }

# Global connection manager instance
connection_manager = ConnectionManager() 