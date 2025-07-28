"""
Real-time Chat WebSocket Messaging.

This module provides WebSocket handlers for real-time chat messaging,
including conversation management and message broadcasting.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.websocket.connection_manager import connection_manager
from app.websocket.auth import WebSocketAuth
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)

class ChatWebSocket:
    """WebSocket handler for real-time chat messaging."""
    
    def __init__(self):
        """Initialize the chat WebSocket handler."""
        self.conversation_participants = {}
        self.message_history = {}
        self.typing_indicators = {}
    
    async def handle_websocket(self, websocket: WebSocket, db: Session):
        """
        Handle WebSocket connection for chat messaging.
        
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
                        # Subscribe to user's chat updates
                        subscription = WebSocketAuth.create_chat_subscription(user.id)
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
                
                elif message["type"] == "chat_message":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_chat_message(websocket, user, message, db)
                
                elif message["type"] == "join_conversation":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_join_conversation(websocket, user, message)
                
                elif message["type"] == "leave_conversation":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_leave_conversation(websocket, user, message)
                
                elif message["type"] == "typing_start":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_typing_start(websocket, user, message)
                
                elif message["type"] == "typing_stop":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_typing_stop(websocket, user, message)
                
                elif message["type"] == "get_conversation_history":
                    if not user:
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "message": "Authentication required",
                            "timestamp": datetime.utcnow().isoformat()
                        }))
                        continue
                    
                    await self._handle_get_conversation_history(websocket, user, message, db)
                
                else:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Unknown message type",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
        
        except WebSocketDisconnect:
            logger.info(f"Chat WebSocket disconnected: {connection_id}")
            if connection_id:
                await connection_manager.disconnect(connection_id, "Client disconnect")
        
        except Exception as e:
            logger.error(f"Chat WebSocket error: {e}")
            if connection_id:
                await connection_manager.disconnect(connection_id, "Error")
    
    async def _handle_chat_message(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle chat message.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Chat message
            db: Database session
        """
        try:
            conversation_id = message.get("conversation_id")
            content = message.get("content")
            message_type = message.get("message_type", "text")
            
            if not conversation_id or not content:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Conversation ID and content required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # Create chat message
            chat_message = {
                "id": f"msg_{datetime.utcnow().timestamp()}",
                "conversation_id": conversation_id,
                "sender_id": user.id,
                "sender_name": user.full_name,
                "sender_email": user.email,
                "content": content,
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in message history
            if conversation_id not in self.message_history:
                self.message_history[conversation_id] = []
            self.message_history[conversation_id].append(chat_message)
            
            # Limit message history
            if len(self.message_history[conversation_id]) > 100:
                self.message_history[conversation_id] = self.message_history[conversation_id][-100:]
            
            # Broadcast to conversation participants
            conversation_subscription = WebSocketAuth.create_chat_subscription(
                user.id, conversation_id
            )
            
            broadcast_message = {
                "type": "chat_message",
                "message": chat_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_manager.broadcast(broadcast_message, conversation_subscription)
            
            # Send confirmation to sender
            await websocket.send_text(json.dumps({
                "type": "message_sent",
                "message_id": chat_message["id"],
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Audit log
            AuditLogger.log_api_call(
                method="websocket",
                path=f"/chat/{conversation_id}",
                user_id=user.id,
                user_email=user.email,
                success=True,
                details={
                    "action": "send_message",
                    "conversation_id": conversation_id,
                    "message_type": message_type
                }
            )
            
            logger.info(f"Chat message sent: {user.id} -> {conversation_id}")
            
        except Exception as e:
            logger.error(f"Handle chat message error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to send message",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_join_conversation(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any]
    ):
        """
        Handle join conversation request.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Join conversation message
        """
        try:
            conversation_id = message.get("conversation_id")
            
            if not conversation_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Conversation ID required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # Add user to conversation participants
            if conversation_id not in self.conversation_participants:
                self.conversation_participants[conversation_id] = set()
            self.conversation_participants[conversation_id].add(user.id)
            
            # Subscribe to conversation
            subscription = WebSocketAuth.create_chat_subscription(user.id, conversation_id)
            await connection_manager.subscribe(connection_manager.get_connection_id(websocket), subscription)
            
            # Send join confirmation
            await websocket.send_text(json.dumps({
                "type": "conversation_joined",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Notify other participants
            join_notification = {
                "type": "user_joined",
                "conversation_id": conversation_id,
                "user_id": user.id,
                "user_name": user.full_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            conversation_subscription = WebSocketAuth.create_chat_subscription(user.id, conversation_id)
            await connection_manager.broadcast(join_notification, conversation_subscription)
            
            logger.info(f"User {user.id} joined conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Join conversation error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to join conversation",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_leave_conversation(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any]
    ):
        """
        Handle leave conversation request.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Leave conversation message
        """
        try:
            conversation_id = message.get("conversation_id")
            
            if not conversation_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Conversation ID required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # Remove user from conversation participants
            if conversation_id in self.conversation_participants:
                self.conversation_participants[conversation_id].discard(user.id)
            
            # Unsubscribe from conversation
            subscription = WebSocketAuth.create_chat_subscription(user.id, conversation_id)
            await connection_manager.unsubscribe(connection_manager.get_connection_id(websocket), subscription)
            
            # Send leave confirmation
            await websocket.send_text(json.dumps({
                "type": "conversation_left",
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            # Notify other participants
            leave_notification = {
                "type": "user_left",
                "conversation_id": conversation_id,
                "user_id": user.id,
                "user_name": user.full_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            conversation_subscription = WebSocketAuth.create_chat_subscription(user.id, conversation_id)
            await connection_manager.broadcast(leave_notification, conversation_subscription)
            
            logger.info(f"User {user.id} left conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Leave conversation error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to leave conversation",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def _handle_typing_start(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any]
    ):
        """
        Handle typing start indicator.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Typing start message
        """
        try:
            conversation_id = message.get("conversation_id")
            
            if not conversation_id:
                return
            
            # Set typing indicator
            typing_key = f"{conversation_id}:{user.id}"
            self.typing_indicators[typing_key] = datetime.utcnow()
            
            # Broadcast typing indicator
            typing_message = {
                "type": "typing_start",
                "conversation_id": conversation_id,
                "user_id": user.id,
                "user_name": user.full_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            conversation_subscription = WebSocketAuth.create_chat_subscription(user.id, conversation_id)
            await connection_manager.broadcast(typing_message, conversation_subscription)
            
        except Exception as e:
            logger.error(f"Typing start error: {e}")
    
    async def _handle_typing_stop(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any]
    ):
        """
        Handle typing stop indicator.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Typing stop message
        """
        try:
            conversation_id = message.get("conversation_id")
            
            if not conversation_id:
                return
            
            # Remove typing indicator
            typing_key = f"{conversation_id}:{user.id}"
            if typing_key in self.typing_indicators:
                del self.typing_indicators[typing_key]
            
            # Broadcast typing stop
            typing_message = {
                "type": "typing_stop",
                "conversation_id": conversation_id,
                "user_id": user.id,
                "user_name": user.full_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            conversation_subscription = WebSocketAuth.create_chat_subscription(user.id, conversation_id)
            await connection_manager.broadcast(typing_message, conversation_subscription)
            
        except Exception as e:
            logger.error(f"Typing stop error: {e}")
    
    async def _handle_get_conversation_history(
        self,
        websocket: WebSocket,
        user: User,
        message: Dict[str, Any],
        db: Session
    ):
        """
        Handle get conversation history request.
        
        Args:
            websocket: WebSocket connection
            user: Authenticated user
            message: Get history message
            db: Database session
        """
        try:
            conversation_id = message.get("conversation_id")
            limit = message.get("limit", 50)
            
            if not conversation_id:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Conversation ID required",
                    "timestamp": datetime.utcnow().isoformat()
                }))
                return
            
            # Get message history
            messages = self.message_history.get(conversation_id, [])
            messages = messages[-limit:] if limit else messages
            
            # Send history
            await websocket.send_text(json.dumps({
                "type": "conversation_history",
                "conversation_id": conversation_id,
                "messages": messages,
                "count": len(messages),
                "timestamp": datetime.utcnow().isoformat()
            }))
            
            logger.info(f"Conversation history sent: {conversation_id} -> {user.id}")
            
        except Exception as e:
            logger.error(f"Get conversation history error: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Failed to get conversation history",
                "timestamp": datetime.utcnow().isoformat()
            }))
    
    async def broadcast_system_message(
        self,
        conversation_id: str,
        message: str,
        message_type: str = "system"
    ):
        """
        Broadcast system message to conversation.
        
        Args:
            conversation_id: Conversation ID
            message: System message
            message_type: Message type
        """
        try:
            system_message = {
                "id": f"sys_{datetime.utcnow().timestamp()}",
                "conversation_id": conversation_id,
                "sender_id": None,
                "sender_name": "System",
                "sender_email": None,
                "content": message,
                "message_type": message_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Store in message history
            if conversation_id not in self.message_history:
                self.message_history[conversation_id] = []
            self.message_history[conversation_id].append(system_message)
            
            # Broadcast to conversation
            broadcast_message = {
                "type": "chat_message",
                "message": system_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Broadcast to all chat subscriptions
            await connection_manager.broadcast(broadcast_message, f"chat:conversation:{conversation_id}")
            
            logger.info(f"System message broadcasted to conversation {conversation_id}")
            
        except Exception as e:
            logger.error(f"Broadcast system message error: {e}")
    
    async def send_direct_message(self, user_id: int, message: Dict[str, Any]):
        """
        Send direct message to user.
        
        Args:
            user_id: User ID
            message: Message to send
        """
        try:
            direct_message = {
                "type": "direct_message",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await connection_manager.send_to_user(user_id, direct_message)
            
            logger.info(f"Direct message sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Send direct message error: {e}")

# Global chat WebSocket handler instance
chat_websocket = ChatWebSocket() 