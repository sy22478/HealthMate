"""
Test WebSocket Integration.

This module tests the WebSocket integration including connection management,
authentication, messaging, and recovery functionality.
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import WebSocket

from app.main import app
from app.websocket.connection_manager import ConnectionManager, ConnectionState
from app.websocket.notifications import NotificationWebSocket, NotificationType, NotificationPriority
from app.websocket.auth import WebSocketAuth
from app.models.user import User

# Test client
client = TestClient(app)

class TestWebSocketIntegration:
    """Test WebSocket integration functionality."""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket for testing."""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for testing."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def connection_manager(self):
        """Create a fresh connection manager for testing."""
        return ConnectionManager()
    
    @pytest.fixture
    def notification_websocket(self):
        """Create a notification WebSocket handler for testing."""
        return NotificationWebSocket()
    
    def test_websocket_endpoints_exist(self):
        """Test that WebSocket endpoints are properly registered."""
        # Check that WebSocket endpoints are available
        response = client.get("/ws/status")
        assert response.status_code == 200
        
        # Check that the response contains expected fields
        data = response.json()
        assert "status" in data
        assert "active_connections" in data
        assert "total_connections" in data
    
    @pytest.mark.asyncio
    async def test_connection_manager_initialization(self, connection_manager):
        """Test connection manager initialization."""
        assert connection_manager.max_connections == 1000
        assert connection_manager.max_connections_per_user == 5
        assert connection_manager.connection_timeout == 3600
        assert connection_manager.heartbeat_interval == 30
        assert connection_manager.cleanup_interval == 300
        assert connection_manager.recovery_interval == 60
        assert connection_manager.max_recovery_attempts == 5
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, connection_manager, mock_websocket):
        """Test WebSocket connection establishment."""
        # Connect WebSocket
        connection_id = await connection_manager.connect(mock_websocket)
        
        # Verify connection was created
        assert connection_id in connection_manager.active_connections
        connection_info = connection_manager.active_connections[connection_id]
        assert connection_info.websocket == mock_websocket
        assert connection_info.state == ConnectionState.CONNECTED
        
        # Verify WebSocket was accepted
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_authentication(self, connection_manager, mock_websocket, mock_user):
        """Test WebSocket connection authentication."""
        # Connect WebSocket
        connection_id = await connection_manager.connect(mock_websocket)
        
        # Mock authentication
        with patch.object(WebSocketAuth, 'handle_authentication_message', return_value=mock_user):
            success = await connection_manager.authenticate_connection(
                connection_id, "test_token", Mock()
            )
        
        # Verify authentication
        assert success
        connection_info = connection_manager.active_connections[connection_id]
        assert connection_info.state == ConnectionState.AUTHENTICATED
        assert connection_info.user_id == mock_user.id
        assert connection_info.user_email == mock_user.email
    
    @pytest.mark.asyncio
    async def test_connection_subscription(self, connection_manager, mock_websocket):
        """Test WebSocket connection subscription."""
        # Connect and authenticate
        connection_id = await connection_manager.connect(mock_websocket)
        connection_info = connection_manager.active_connections[connection_id]
        connection_info.user_id = 1
        connection_info.state = ConnectionState.AUTHENTICATED
        
        # Subscribe to a channel
        subscription = "health_updates"
        success = await connection_manager.subscribe(connection_id, subscription)
        
        # Verify subscription
        assert success
        assert subscription in connection_info.subscriptions
        assert connection_id in connection_manager.subscription_connections[subscription]
    
    @pytest.mark.asyncio
    async def test_message_broadcasting(self, connection_manager, mock_websocket):
        """Test message broadcasting to subscribed connections."""
        # Connect and subscribe
        connection_id = await connection_manager.connect(mock_websocket)
        subscription = "health_updates"
        await connection_manager.subscribe(connection_id, subscription)
        
        # Broadcast message
        message = {"type": "health_update", "data": "test"}
        await connection_manager.broadcast(message, subscription)
        
        # Verify message was sent
        mock_websocket.send_text.assert_called_once()
        sent_message = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_message["type"] == "health_update"
        assert sent_message["data"] == "test"
    
    @pytest.mark.asyncio
    async def test_connection_disconnect(self, connection_manager, mock_websocket):
        """Test WebSocket connection disconnection."""
        # Connect WebSocket
        connection_id = await connection_manager.connect(mock_websocket)
        assert connection_id in connection_manager.active_connections
        
        # Disconnect
        await connection_manager.disconnect(connection_id, "Test disconnect")
        
        # Verify connection was removed
        assert connection_id not in connection_manager.active_connections
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connection_recovery(self, connection_manager, mock_websocket):
        """Test connection recovery functionality."""
        # Connect WebSocket
        connection_id = await connection_manager.connect(mock_websocket)
        connection_info = connection_manager.active_connections[connection_id]
        
        # Simulate connection error
        connection_info.state = ConnectionState.ERROR
        connection_info.last_error = "Test error"
        
        # Attempt recovery
        await connection_manager._attempt_connection_recovery(connection_id)
        
        # Verify recovery attempt
        assert connection_info.recovery_attempts == 1
        
        # Simulate successful recovery
        mock_websocket.send_text.side_effect = None
        await connection_manager._attempt_connection_recovery(connection_id)
        
        # Verify recovery success
        assert connection_info.state == ConnectionState.CONNECTED
        assert connection_info.last_error is None
        assert connection_info.recovery_attempts == 0
    
    @pytest.mark.asyncio
    async def test_retry_send_message(self, connection_manager, mock_websocket):
        """Test message sending with retry logic."""
        # Connect WebSocket
        connection_id = await connection_manager.connect(mock_websocket)
        
        # Test successful send
        message = {"type": "test", "data": "test"}
        success = await connection_manager.retry_send_message(connection_id, message)
        
        # Verify successful send
        assert success
        mock_websocket.send_text.assert_called_once()
        
        # Test failed send with retries
        mock_websocket.send_text.side_effect = Exception("Send error")
        success = await connection_manager.retry_send_message(connection_id, message, max_retries=2)
        
        # Verify failed send after retries
        assert not success
        connection_info = connection_manager.active_connections[connection_id]
        assert connection_info.state == ConnectionState.ERROR
    
    @pytest.mark.asyncio
    async def test_notification_websocket_initialization(self, notification_websocket):
        """Test notification WebSocket initialization."""
        assert notification_websocket.notification_queue == {}
        assert notification_websocket.user_preferences == {}
        assert notification_websocket.audit_logger is not None
    
    @pytest.mark.asyncio
    async def test_notification_sending(self, notification_websocket, mock_websocket):
        """Test notification sending functionality."""
        # Mock connection manager
        with patch('app.websocket.notifications.connection_manager') as mock_cm:
            mock_cm.send_to_user.return_value = True
            
            # Send notification
            await notification_websocket.send_notification(
                user_id=1,
                notification_type=NotificationType.HEALTH_ALERT,
                title="Test Alert",
                message="Test message",
                priority=NotificationPriority.HIGH
            )
            
            # Verify notification was sent
            mock_cm.send_to_user.assert_called_once()
            call_args = mock_cm.send_to_user.call_args[0]
            assert call_args[0] == 1  # user_id
            assert call_args[1]["type"] == "notification"
            assert call_args[1]["notification"]["title"] == "Test Alert"
    
    @pytest.mark.asyncio
    async def test_notification_preferences(self, notification_websocket):
        """Test notification preference handling."""
        # Set user preferences
        user_id = 1
        preferences = {
            NotificationType.HEALTH_ALERT.value: {
                "enabled": True,
                "min_priority": NotificationPriority.HIGH.value
            }
        }
        notification_websocket.user_preferences[user_id] = preferences
        
        # Test priority filtering
        # High priority notification should be sent
        high_priority = notification_websocket._is_priority_higher_or_equal(
            NotificationPriority.HIGH.value,
            NotificationPriority.HIGH.value
        )
        assert high_priority is True
        
        # Low priority notification should not be sent
        low_priority = notification_websocket._is_priority_higher_or_equal(
            NotificationPriority.LOW.value,
            NotificationPriority.HIGH.value
        )
        assert low_priority is False
    
    def test_connection_stats(self, connection_manager):
        """Test connection statistics generation."""
        stats = connection_manager.get_connection_stats()
        
        # Verify stats structure
        assert "total_connections" in stats
        assert "authenticated_connections" in stats
        assert "total_subscriptions" in stats
        assert "total_users" in stats
        assert "max_connections" in stats
        assert "max_connections_per_user" in stats
        assert "connection_timeout" in stats
        assert "heartbeat_interval" in stats
        assert "recovery_interval" in stats
        assert "max_recovery_attempts" in stats
    
    @pytest.mark.asyncio
    async def test_connection_health_monitoring(self, connection_manager, mock_websocket):
        """Test connection health monitoring."""
        # Connect WebSocket
        connection_id = await connection_manager.connect(mock_websocket)
        connection_info = connection_manager.active_connections[connection_id]
        connection_info.user_id = 1
        connection_info.state = ConnectionState.AUTHENTICATED
        
        # Get health information
        health = connection_manager.get_connection_health(connection_id)
        
        # Verify health information
        assert health["connection_id"] == connection_id
        assert health["state"] == ConnectionState.AUTHENTICATED.value
        assert health["user_id"] == 1
        assert health["is_healthy"] is True
        assert "connected_at" in health
        assert "last_activity" in health
        assert "retry_count" in health
        assert "recovery_attempts" in health
        assert "subscriptions" in health
    
    @pytest.mark.asyncio
    async def test_user_reconnection(self, connection_manager, mock_websocket):
        """Test user reconnection functionality."""
        # Connect multiple WebSockets for same user
        connection_id1 = await connection_manager.connect(mock_websocket)
        connection_id2 = await connection_manager.connect(Mock(spec=WebSocket))
        
        # Set up connections for same user
        connection_info1 = connection_manager.active_connections[connection_id1]
        connection_info2 = connection_manager.active_connections[connection_id2]
        connection_info1.user_id = 1
        connection_info2.user_id = 1
        connection_info1.state = ConnectionState.ERROR
        connection_info2.state = ConnectionState.AUTHENTICATED
        
        # Attempt reconnection
        success = await connection_manager.reconnect_user(1)
        
        # Verify reconnection attempt
        assert success is False  # Should fail due to mock WebSocket
    
    def test_websocket_router_endpoints(self):
        """Test that WebSocket router endpoints are properly configured."""
        # Test status endpoint
        response = client.get("/ws/status")
        assert response.status_code == 200
        
        # Test connection health endpoint (should return 404 for non-existent connection)
        response = client.get("/ws/connection/nonexistent/health")
        assert response.status_code == 200  # Returns health info with not_found status
        
        # Test user reconnection endpoint
        response = client.post("/ws/user/1/reconnect")
        assert response.status_code == 200
        
        # Test connection disconnect endpoint
        response = client.delete("/ws/connection/nonexistent")
        assert response.status_code == 200

class TestWebSocketIntegrationEndToEnd:
    """End-to-end WebSocket integration tests."""
    
    def test_websocket_flow(self):
        """Test complete WebSocket flow from connection to messaging."""
        # This would require a real WebSocket client for end-to-end testing
        # For now, we'll test the API endpoints
        
        # Test WebSocket status
        response = client.get("/ws/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "active_connections" in data
        
        # Test connection health for non-existent connection
        response = client.get("/ws/connection/test-connection/health")
        assert response.status_code == 200
        data = response.json()
        assert data["health"]["status"] == "not_found"
        
        # Test user reconnection
        response = client.post("/ws/user/999/reconnect")
        assert response.status_code == 200
        data = response.json()
        assert "reconnected" in data
        assert "user_id" in data
    
    def test_websocket_error_handling(self):
        """Test WebSocket error handling."""
        # Test with invalid connection ID
        response = client.get("/ws/connection/invalid-uuid/health")
        assert response.status_code == 200
        
        # Test with invalid user ID
        response = client.post("/ws/user/invalid/reconnect")
        assert response.status_code == 422  # Validation error
        
        # Test connection disconnect with invalid ID
        response = client.delete("/ws/connection/invalid-uuid")
        assert response.status_code == 200

if __name__ == "__main__":
    pytest.main([__file__]) 