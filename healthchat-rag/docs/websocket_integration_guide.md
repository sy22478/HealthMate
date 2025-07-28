# WebSocket Integration Guide

This document provides a comprehensive guide to the WebSocket integration system implemented in HealthMate, covering real-time communication, connection management, and data synchronization.

## Overview

The WebSocket integration system provides real-time communication capabilities for the HealthMate application, enabling:

- **Real-time health data updates**: Live streaming of health metrics and alerts
- **Chat messaging**: Real-time chat conversations with AI health assistant
- **Notification delivery**: Instant delivery of health alerts and reminders
- **Connection management**: Robust connection handling with recovery and scaling

## Architecture

### Core Components

1. **Connection Manager** (`app/websocket/connection_manager.py`)
   - Manages WebSocket connections with pooling and scaling
   - Handles authentication and authorization
   - Provides connection recovery and retry logic
   - Monitors connection health and statistics

2. **WebSocket Handlers**
   - **Health Updates** (`app/websocket/health_updates.py`): Real-time health data streaming
   - **Chat Messaging** (`app/websocket/chat_messaging.py`): Real-time chat functionality
   - **Notifications** (`app/websocket/notifications.py`): Notification delivery system

3. **Authentication** (`app/websocket/auth.py`)
   - WebSocket-specific authentication and authorization
   - Token validation and user verification
   - Subscription management

4. **Router** (`app/routers/websocket.py`)
   - FastAPI WebSocket endpoints
   - Connection management APIs
   - Health monitoring endpoints

## WebSocket Endpoints

### Real-time Communication Endpoints

#### Health Data WebSocket
```
GET /ws/health
```
Handles real-time health data updates, metrics streaming, and health alerts.

**Features:**
- Live health metrics streaming
- Real-time health alerts
- Health data synchronization
- Threshold-based notifications

#### Chat WebSocket
```
GET /ws/chat
```
Manages real-time chat conversations with the AI health assistant.

**Features:**
- Real-time message exchange
- Typing indicators
- Message broadcasting
- Conversation history

#### Notification WebSocket
```
GET /ws/notifications
```
Delivers real-time notifications and alerts to users.

**Features:**
- Health alerts and notifications
- Medication reminders
- Appointment reminders
- System notifications
- Notification preferences management

#### Combined WebSocket
```
GET /ws/combined
```
Single WebSocket connection for all real-time features (future implementation).

### Management Endpoints

#### Connection Status
```
GET /ws/status
```
Returns WebSocket connection statistics and system health.

**Response:**
```json
{
  "status": "healthy",
  "active_connections": 10,
  "total_connections": 150,
  "users_online": 8,
  "subscriptions": {
    "health_updates": 5,
    "chat": 3,
    "notifications": 8
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### Connection Health
```
GET /ws/connection/{connection_id}/health
```
Returns detailed health information for a specific connection.

**Response:**
```json
{
  "connection_id": "uuid",
  "health": {
    "state": "authenticated",
    "user_id": 1,
    "connected_at": "2024-01-01T00:00:00Z",
    "last_activity": "2024-01-01T00:05:00Z",
    "retry_count": 0,
    "recovery_attempts": 0,
    "subscriptions": ["health_updates", "notifications"],
    "is_healthy": true
  }
}
```

#### User Reconnection
```
POST /ws/user/{user_id}/reconnect
```
Attempts to reconnect all connections for a specific user.

#### Connection Disconnect
```
DELETE /ws/connection/{connection_id}
```
Manually disconnects a WebSocket connection.

## Connection Management

### Connection Lifecycle

1. **Connection Establishment**
   - Client connects to WebSocket endpoint
   - Connection is accepted and assigned unique ID
   - Welcome message sent to client

2. **Authentication**
   - Client sends authentication message with JWT token
   - Token is validated and user is verified
   - Connection state updated to "authenticated"

3. **Subscription Management**
   - Client subscribes to specific channels (health, chat, notifications)
   - Connection is added to subscription pools
   - Real-time updates begin

4. **Message Exchange**
   - Bidirectional message exchange
   - Heartbeat messages maintain connection
   - Error handling and recovery

5. **Connection Termination**
   - Client disconnects or connection times out
   - Resources are cleaned up
   - User is removed from subscription pools

### Connection States

- **CONNECTING**: Initial connection state
- **CONNECTED**: WebSocket connected, not authenticated
- **AUTHENTICATED**: User authenticated and ready for communication
- **ERROR**: Connection in error state, recovery attempts possible
- **DISCONNECTED**: Connection terminated

### Connection Pooling and Scaling

The connection manager supports:
- **Maximum connections**: 1000 concurrent connections
- **Per-user limits**: 5 connections per user
- **Connection timeout**: 1 hour idle timeout
- **Heartbeat interval**: 30 seconds
- **Cleanup interval**: 5 minutes
- **Recovery interval**: 1 minute

## Message Format

### Standard Message Structure

All WebSocket messages follow a standard JSON format:

```json
{
  "type": "message_type",
  "data": {},
  "timestamp": "2024-01-01T00:00:00Z",
  "correlation_id": "uuid"
}
```

### Message Types

#### Authentication Messages
```json
{
  "type": "authenticate",
  "token": "jwt_token_here"
}
```

#### Health Data Messages
```json
{
  "type": "health_update",
  "data": {
    "metric": "blood_pressure",
    "value": 120,
    "unit": "mmHg",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

#### Chat Messages
```json
{
  "type": "chat_message",
  "data": {
    "message": "Hello, how can I help you?",
    "sender": "ai_assistant",
    "conversation_id": "uuid"
  }
}
```

#### Notification Messages
```json
{
  "type": "notification",
  "notification": {
    "id": "uuid",
    "type": "health_alert",
    "title": "Blood Pressure Alert",
    "message": "Your blood pressure is above normal range",
    "priority": "high",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

## Error Handling and Recovery

### Error Types

1. **Connection Errors**
   - Network disconnections
   - Timeout errors
   - Protocol errors

2. **Authentication Errors**
   - Invalid tokens
   - Expired tokens
   - Authorization failures

3. **Message Errors**
   - Invalid message format
   - Missing required fields
   - Validation errors

### Recovery Mechanisms

1. **Automatic Reconnection**
   - Failed connections are automatically retried
   - Exponential backoff prevents overwhelming the server
   - Maximum retry attempts prevent infinite loops

2. **Connection Recovery**
   - Background task monitors failed connections
   - Attempts to recover connections in error state
   - Graceful degradation when recovery fails

3. **Message Retry**
   - Failed message sends are retried with exponential backoff
   - Message queuing for offline users
   - Guaranteed delivery for critical messages

## Security

### Authentication and Authorization

- **JWT Token Validation**: All WebSocket connections require valid JWT tokens
- **User Verification**: Users are verified against the database
- **Role-based Access**: Different subscription levels based on user roles
- **Token Refresh**: Automatic token refresh for long-lived connections

### Data Protection

- **Message Encryption**: All messages are encrypted in transit
- **Input Validation**: All incoming messages are validated and sanitized
- **Rate Limiting**: Prevents abuse and DoS attacks
- **Audit Logging**: All WebSocket activities are logged for security

## Performance and Scalability

### Performance Optimizations

1. **Connection Pooling**
   - Efficient connection management
   - Resource sharing across connections
   - Memory optimization

2. **Message Broadcasting**
   - Efficient message routing to subscribed users
   - Batch message processing
   - Optimized serialization

3. **Background Tasks**
   - Asynchronous processing
   - Non-blocking operations
   - Resource cleanup

### Scalability Features

1. **Horizontal Scaling**
   - Stateless connection management
   - Shared subscription pools
   - Load balancer support

2. **Resource Management**
   - Connection limits and quotas
   - Memory usage monitoring
   - Automatic cleanup

3. **Monitoring and Metrics**
   - Real-time connection statistics
   - Performance metrics
   - Health monitoring

## Testing

### Test Coverage

The WebSocket integration includes comprehensive tests:

1. **Unit Tests**
   - Connection manager functionality
   - Message handling
   - Authentication and authorization
   - Error handling

2. **Integration Tests**
   - End-to-end WebSocket flows
   - API endpoint testing
   - Error scenario testing

3. **Performance Tests**
   - Connection scaling
   - Message throughput
   - Memory usage

### Running Tests

```bash
# Run all WebSocket tests
python -m pytest tests/test_websocket_integration.py -v

# Run specific test categories
python -m pytest tests/test_websocket_integration.py::TestWebSocketIntegration -v
python -m pytest tests/test_websocket_integration.py::TestWebSocketIntegrationEndToEnd -v
```

## Usage Examples

### JavaScript Client Example

```javascript
// Connect to health WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/health');

// Authenticate
ws.onopen = function() {
    ws.send(JSON.stringify({
        type: 'authenticate',
        token: 'your_jwt_token_here'
    }));
};

// Handle messages
ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'health_update':
            console.log('Health update:', message.data);
            break;
        case 'notification':
            console.log('Notification:', message.notification);
            break;
        case 'heartbeat':
            console.log('Heartbeat received');
            break;
    }
};

// Handle errors
ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

// Handle disconnection
ws.onclose = function(event) {
    console.log('WebSocket closed:', event.code, event.reason);
};
```

### Python Client Example

```python
import asyncio
import websockets
import json

async def health_websocket_client():
    uri = "ws://localhost:8000/ws/health"
    
    async with websockets.connect(uri) as websocket:
        # Authenticate
        auth_message = {
            "type": "authenticate",
            "token": "your_jwt_token_here"
        }
        await websocket.send(json.dumps(auth_message))
        
        # Subscribe to health updates
        subscribe_message = {
            "type": "subscribe",
            "subscription": "health_updates"
        }
        await websocket.send(json.dumps(subscribe_message))
        
        # Listen for messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")

# Run client
asyncio.run(health_websocket_client())
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Check if WebSocket server is running
   - Verify endpoint URL and port
   - Check firewall settings

2. **Authentication Failures**
   - Verify JWT token is valid and not expired
   - Check token format and signature
   - Ensure user exists in database

3. **Message Delivery Issues**
   - Check subscription status
   - Verify message format
   - Check connection state

4. **Performance Issues**
   - Monitor connection count
   - Check memory usage
   - Review message frequency

### Debugging

1. **Enable Debug Logging**
   ```python
   import logging
   logging.getLogger('app.websocket').setLevel(logging.DEBUG)
   ```

2. **Check Connection Status**
   ```bash
   curl http://localhost:8000/ws/status
   ```

3. **Monitor Connection Health**
   ```bash
   curl http://localhost:8000/ws/connection/{connection_id}/health
   ```

## Future Enhancements

### Planned Features

1. **Advanced Message Routing**
   - Topic-based subscriptions
   - Message filtering
   - Custom routing rules

2. **Enhanced Security**
   - End-to-end encryption
   - Certificate pinning
   - Advanced authentication methods

3. **Performance Improvements**
   - Message compression
   - Binary message format
   - Connection multiplexing

4. **Monitoring and Analytics**
   - Real-time dashboards
   - Performance metrics
   - Usage analytics

### Integration Opportunities

1. **External Services**
   - Push notification services
   - Message queues
   - Event streaming platforms

2. **Mobile Applications**
   - Native WebSocket clients
   - Offline message queuing
   - Background sync

3. **Third-party Integrations**
   - Health device APIs
   - EHR systems
   - Telemedicine platforms

## Conclusion

The WebSocket integration system provides a robust foundation for real-time communication in the HealthMate application. With comprehensive connection management, error handling, and security features, it enables seamless real-time experiences for users while maintaining system reliability and scalability.

For additional support or questions, please refer to the API documentation or contact the development team. 