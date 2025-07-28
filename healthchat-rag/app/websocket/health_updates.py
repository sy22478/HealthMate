"""
Real-time Health Data WebSocket Updates.

This module provides WebSocket handlers for real-time health data updates,
including live data synchronization and health monitoring alerts.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.health_data import HealthData
from app.models.user import User
from app.websocket.connection_manager import connection_manager
from app.websocket.auth import WebSocketAuth
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)

class HealthDataWebSocket:
    """WebSocket handler for real-time health data updates."""
    
    def __init__(self):
        """Initialize the health data WebSocket handler."""
        self.health_alerts = {}
        self.data_thresholds = {
            "blood_pressure": {"systolic": {"min": 90, "max": 140}, "diastolic": {"min": 60, "max": 90}},
            "heart_rate": {"min": 60, "max": 100},
            "blood_sugar": {"min": 70, "max": 140},
            "temperature": {"min": 97.0, "max": 99.5},
            "weight": {"min": 30, "max": 300}
        }
    
    async def handle_websocket(self, websocket: WebSocket, db: Session):
        """
        Handle WebSocket connection for health data updates.
        
        Args:
            websocket: WebSocket connection
            db: Database session
        """
        connection_id = None
        user = None
        
        try:
            # Accept connection
            connection_id = await connection_manager.connect(websocket)
            
            # Handle messages
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Validate message format
                if not WebSocketAuth.validate_message_format(message):
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Invalid message format",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                    continue
                
                # Handle message based on type
                if message["type"] == "authentication":
                    user = await WebSocketAuth.handle_authentication_message(
                        websocket, message, db
                    )
                    if user:
                        # Subscribe to user's health data updates
                        subscription = WebSocketAuth.create_health_data_subscription(user.id)
                        await connection_manager.subscribe(connection_id, subscription)
                
                elif message["type"] == "subscribe":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    success = await WebSocketAuth.handle_subscription_message(
                        websocket, message, user
                    )
                    if success:
                        subscription = message.get("subscription")
                        await connection_manager.subscribe(connection_id, subscription)
                
                elif message["type"] == "unsubscribe":
                    subscription = message.get("subscription")
                    if subscription:
                        await connection_manager.unsubscribe(connection_id, subscription)
                
                elif message["type"] == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
                elif message["type"] == "get_health_data":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_get_health_data(websocket, user, message, db)
                
                elif message["type"] == "set_alert_threshold":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_set_alert_threshold(websocket, user, message)
                
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Unknown message type",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {connection_id}")
            if connection_id:
                await connection_manager.disconnect(connection_id, "Client disconnect")
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if connection_id:
                await connection_manager.disconnect(connection_id, "Error")
    
    async def _handle_get_health_data(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle get health data request.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Request message
            db: Database session
        """
        try:
            data_type = message.get("data_type")
            limit = message.get("limit", 10)
            
            # Build query
            query = db.query(HealthData).filter(HealthData.user_id == user.id)
            
            if data_type:
                query = query.filter(HealthData.data_type == data_type)
            
            # Get recent health data
            health_data_list = query.order_by(HealthData.timestamp.desc()).limit(limit).all()
            
            # Convert to response format
            data = []
            for health_data in health_data_list:
                data.append({
                    "id": health_data.id,
                    "data_type": health_data.data_type,
                    "value": health_data.value,
                    "unit": health_data.unit,
                    "timestamp": health_data.timestamp.isoformat(),
                    "notes": health_data.notes
                })
            
            # Send response
            await websocket.send_text(json.dumps({
                "type": "health_data_response",
                "data": data,
                "data_type": data_type,
                "count": len(data),
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Audit log
            AuditLogger.log_health_data_access(
                action="read",
                user_id=user.id,
                user_email=user.email,
                data_type=data_type or "all",
                success=True,
                details={"websocket": True, "count": len(data)}
            )
            
        except Exception as e:
            logger.error(f"Get health data error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to get health data",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_set_alert_threshold(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any]
    ):
        """
        Handle set alert threshold request.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Request message
        """
        try:
            data_type = message.get("data_type")
            threshold = message.get("threshold")
            
            if not data_type or not threshold:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Data type and threshold required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # Store user-specific threshold
            user_key = f"{user.id}:{data_type}"
            self.health_alerts[user_key] = threshold
            
            await websocket.send_text(json.dumps({
                "type": "alert_threshold_set",
                "data_type": data_type,
                "threshold": threshold,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            logger.info(f"Alert threshold set for user {user.id}: {data_type} = {threshold}")
            
        except Exception as e:
            logger.error(f"Set alert threshold error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to set alert threshold",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def broadcast_health_update(self, health_data: HealthData):
        """
        Broadcast health data update to subscribed users.
        
        Args:
            health_data: Health data record
        """
        try:
            # Create update message
            update_message = {
                "type": "health_data_update",
                "data": {
                    "id": health_data.id,
                    "data_type": health_data.data_type,
                    "value": health_data.value,
                    "unit": health_data.unit,
                    "timestamp": health_data.timestamp.isoformat(),
                    "notes": health_data.notes
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to user-specific subscription
            user_subscription = WebSocketAuth.create_health_data_subscription(health_data.user_id)
            await connection_manager.broadcast(update_message, user_subscription)
            
            # Check for alerts
            await self._check_health_alerts(health_data)
            
            logger.info(f"Health data update broadcasted for user {health_data.user_id}")
            
        except Exception as e:
            logger.error(f"Broadcast health update error: {e}")
    
    async def _check_health_alerts(self, health_data: HealthData):
        """
        Check health data for alerts and send notifications.
        
        Args:
            health_data: Health data record
        """
        try:
            data_type = health_data.data_type
            value = health_data.value
            
            # Get thresholds
            default_thresholds = self.data_thresholds.get(data_type, {})
            user_key = f"{health_data.user_id}:{data_type}"
            user_thresholds = self.health_alerts.get(user_key, default_thresholds)
            
            # Check for alerts
            alert_triggered = False
            alert_message = ""
            
            if isinstance(user_thresholds, dict):
                if "min" in user_thresholds and value < user_thresholds["min"]:
                    alert_triggered = True
                    alert_message = f"{data_type} value {value} is below minimum threshold {user_thresholds['min']}"
                elif "max" in user_thresholds and value > user_thresholds["max"]:
                    alert_triggered = True
                    alert_message = f"{data_type} value {value} is above maximum threshold {user_thresholds['max']}"
                
                # Check systolic/diastolic for blood pressure
                if data_type == "blood_pressure" and isinstance(value, dict):
                    systolic = value.get("systolic")
                    diastolic = value.get("diastolic")
                    
                    if systolic and diastolic:
                        if systolic < user_thresholds.get("systolic", {}).get("min", 90):
                            alert_triggered = True
                            alert_message = f"Blood pressure systolic {systolic} is below minimum threshold"
                        elif systolic > user_thresholds.get("systolic", {}).get("max", 140):
                            alert_triggered = True
                            alert_message = f"Blood pressure systolic {systolic} is above maximum threshold"
                        elif diastolic < user_thresholds.get("diastolic", {}).get("min", 60):
                            alert_triggered = True
                            alert_message = f"Blood pressure diastolic {diastolic} is below minimum threshold"
                        elif diastolic > user_thresholds.get("diastolic", {}).get("max", 90):
                            alert_triggered = True
                            alert_message = f"Blood pressure diastolic {diastolic} is above maximum threshold"
            
            # Send alert if triggered
            if alert_triggered:
                alert_message_data = {
                    "type": "health_alert",
                    "alert": {
                        "data_type": data_type,
                        "value": value,
                        "message": alert_message,
                        "severity": "warning",
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Send to user
                await connection_manager.send_to_user(health_data.user_id, alert_message_data)
                
                # Also send to notification subscription
                notification_subscription = WebSocketAuth.create_notification_subscription(
                    health_data.user_id, "health_alerts"
                )
                await connection_manager.broadcast(alert_message_data, notification_subscription)
                
                logger.warning(f"Health alert sent to user {health_data.user_id}: {alert_message}")
                
        except Exception as e:
            logger.error(f"Check health alerts error: {e}")
    
    async def send_health_summary(self, user_id: int, summary_data: Dict[str, Any]):
        """
        Send health summary to user.
        
        Args:
            user_id: User ID
            summary_data: Health summary data
        """
        try:
            summary_message = {
                "type": "health_summary",
                "summary": summary_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_manager.send_to_user(user_id, summary_message)
            
            logger.info(f"Health summary sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Send health summary error: {e}")

# Global health data WebSocket handler instance
health_data_websocket = HealthDataWebSocket() 