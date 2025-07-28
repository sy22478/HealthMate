"""
WebSocket Router for FastAPI.

This module provides WebSocket endpoints for real-time communication
including health data updates, chat messaging, and notifications.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.websocket.health_updates import health_data_websocket
from app.websocket.chat_messaging import chat_websocket
from app.websocket.notifications import notification_websocket
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

# Create WebSocket router
websocket_router = APIRouter()

@websocket_router.websocket("/ws/health")
async def health_websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time health data updates.
    
    This endpoint handles:
    - Health data live updates
    - Real-time health metrics
    - Health alerts and notifications
    - Health data synchronization
    """
    try:
        await health_data_websocket.handle_websocket(websocket, db)
    except WebSocketDisconnect:
        logger.info("Health WebSocket disconnected")
    except Exception as e:
        logger.error(f"Health WebSocket error: {e}")
        audit_logger.log_system_action(
            action="websocket_error",
            details={"endpoint": "/ws/health", "error": str(e)}
        )

@websocket_router.websocket("/ws/chat")
async def chat_websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time chat messaging.
    
    This endpoint handles:
    - Real-time chat messages
    - Typing indicators
    - Message broadcasting
    - Chat conversation management
    """
    try:
        await chat_websocket.handle_websocket(websocket, db)
    except WebSocketDisconnect:
        logger.info("Chat WebSocket disconnected")
    except Exception as e:
        logger.error(f"Chat WebSocket error: {e}")
        audit_logger.log_system_action(
            action="websocket_error",
            details={"endpoint": "/ws/chat", "error": str(e)}
        )

@websocket_router.websocket("/ws/notifications")
async def notification_websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for real-time notification delivery.
    
    This endpoint handles:
    - Health alerts and notifications
    - Medication reminders
    - Appointment reminders
    - System notifications
    - Notification preferences
    """
    try:
        await notification_websocket.handle_websocket(websocket, db)
    except WebSocketDisconnect:
        logger.info("Notification WebSocket disconnected")
    except Exception as e:
        logger.error(f"Notification WebSocket error: {e}")
        audit_logger.log_system_action(
            action="websocket_error",
            details={"endpoint": "/ws/notifications", "error": str(e)}
        )

@websocket_router.websocket("/ws/combined")
async def combined_websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Combined WebSocket endpoint for all real-time features.
    
    This endpoint provides a single connection for:
    - Health data updates
    - Chat messaging
    - Notifications
    - System events
    """
    try:
        # Accept connection
        await websocket.accept()
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "Connected to HealthMate real-time services",
            "services": ["health", "chat", "notifications"],
            "timestamp": "2024-01-01T00:00:00Z"
        }))
        
        # TODO: Implement combined WebSocket handler
        # This would route messages to appropriate handlers based on message type
        
        while True:
            try:
                # Keep connection alive
                data = await websocket.receive_text()
                # Process message and route to appropriate handler
                await websocket.send_text(json.dumps({
                    "type": "acknowledgment",
                    "message": "Message received",
                    "timestamp": "2024-01-01T00:00:00Z"
                }))
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("Combined WebSocket disconnected")
    except Exception as e:
        logger.error(f"Combined WebSocket error: {e}")
        audit_logger.log_system_action(
            action="websocket_error",
            details={"endpoint": "/ws/combined", "error": str(e)}
        )

# WebSocket status endpoint
@websocket_router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection status and statistics.
    
    Returns:
        Dictionary containing WebSocket connection statistics
    """
    try:
        from app.websocket.connection_manager import connection_manager
        
        stats = connection_manager.get_connection_stats()
        
        return {
            "status": "healthy",
            "active_connections": stats.get("active_connections", 0),
            "total_connections": stats.get("total_connections", 0),
            "users_online": stats.get("users_online", 0),
            "subscriptions": stats.get("subscriptions", {}),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket status: {e}")
        return {
            "status": "error",
            "message": "Failed to get WebSocket status",
            "timestamp": "2024-01-01T00:00:00Z"
        }

# Connection health endpoint
@websocket_router.get("/ws/connection/{connection_id}/health")
async def connection_health(connection_id: str):
    """
    Get health information for a specific WebSocket connection.
    
    Args:
        connection_id: Connection ID to check
        
    Returns:
        Connection health information
    """
    try:
        from app.websocket.connection_manager import connection_manager
        
        health_info = connection_manager.get_connection_health(connection_id)
        
        return {
            "connection_id": connection_id,
            "health": health_info,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error getting connection health: {e}")
        return {
            "connection_id": connection_id,
            "status": "error",
            "message": "Failed to get connection health",
            "timestamp": "2024-01-01T00:00:00Z"
        }

# User reconnection endpoint
@websocket_router.post("/ws/user/{user_id}/reconnect")
async def reconnect_user_connections(user_id: int):
    """
    Attempt to reconnect all connections for a specific user.
    
    Args:
        user_id: User ID to reconnect
        
    Returns:
        Reconnection result
    """
    try:
        from app.websocket.connection_manager import connection_manager
        
        success = await connection_manager.reconnect_user(user_id)
        
        return {
            "user_id": user_id,
            "reconnected": success,
            "message": "User reconnection attempted",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error reconnecting user {user_id}: {e}")
        return {
            "user_id": user_id,
            "reconnected": False,
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

# Connection management endpoint
@websocket_router.delete("/ws/connection/{connection_id}")
async def disconnect_connection(connection_id: str, reason: str = "Admin disconnect"):
    """
    Manually disconnect a WebSocket connection.
    
    Args:
        connection_id: Connection ID to disconnect
        reason: Reason for disconnection
        
    Returns:
        Disconnection result
    """
    try:
        from app.websocket.connection_manager import connection_manager
        
        await connection_manager.disconnect(connection_id, reason)
        
        return {
            "connection_id": connection_id,
            "disconnected": True,
            "reason": reason,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Error disconnecting connection {connection_id}: {e}")
        return {
            "connection_id": connection_id,
            "disconnected": False,
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        } 