"""
Webhook Management Router for HealthMate

This module provides:
- Webhook endpoint registration
- Webhook signature verification
- Webhook event processing pipeline
- Webhook failure handling and retry
- Webhook management APIs
"""

import logging
import json
import uuid
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl, validator

from app.database import get_db
from app.models.user import User
from app.utils.auth_middleware import get_current_user
from app.services.external_api_client import (
    ExternalAPIClient, APIConfig, OAuth2Config, AuthenticationType,
    WebhookEvent, WebhookManager
)
from app.utils.audit_logging import AuditLogger
from app.utils.encryption_utils import field_encryption

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()

# Create webhook router
webhook_router = APIRouter()


# Pydantic models for webhook management
class WebhookRegistrationRequest(BaseModel):
    """Request model for webhook registration."""
    url: HttpUrl
    events: List[str]
    secret: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True
    retry_count: int = 3
    retry_delay_seconds: int = 60
    timeout_seconds: int = 30
    
    @validator('events')
    def validate_events(cls, v):
        """Validate webhook events."""
        valid_events = {
            'user.registered', 'user.login', 'user.logout',
            'health_metric.added', 'health_metric.updated', 'health_metric.deleted',
            'chat.message.sent', 'chat.message.received',
            'notification.sent', 'notification.delivered', 'notification.failed',
            'medication.reminder', 'appointment.reminder',
            'emergency.alert', 'goal.achieved', 'goal.updated',
            'data.exported', 'data.deleted', 'compliance.alert'
        }
        
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid event type: {event}")
        
        return v


class WebhookRegistrationResponse(BaseModel):
    """Response model for webhook registration."""
    webhook_id: str
    url: str
    events: List[str]
    status: str
    created_at: datetime
    secret: Optional[str] = None


class WebhookUpdateRequest(BaseModel):
    """Request model for webhook updates."""
    url: Optional[HttpUrl] = None
    events: Optional[List[str]] = None
    secret: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    retry_count: Optional[int] = None
    retry_delay_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None


class WebhookDeliveryAttempt(BaseModel):
    """Model for webhook delivery attempt."""
    attempt_id: str
    webhook_id: str
    event_type: str
    event_id: str
    status: str
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    attempt_number: int
    created_at: datetime
    completed_at: Optional[datetime] = None


class WebhookStatusResponse(BaseModel):
    """Response model for webhook status."""
    webhook_id: str
    url: str
    events: List[str]
    status: str
    enabled: bool
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
    last_delivery: Optional[datetime] = None
    last_error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# In-memory storage for webhooks (in production, use database)
webhook_registry: Dict[str, Dict[str, Any]] = {}
webhook_delivery_log: Dict[str, List[Dict[str, Any]]] = {}


@webhook_router.post("/register", response_model=WebhookRegistrationResponse)
async def register_webhook(
    request: WebhookRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new webhook endpoint.
    
    This endpoint allows external systems to register webhook endpoints
    that will receive real-time notifications from HealthMate.
    """
    try:
        # Generate webhook ID
        webhook_id = str(uuid.uuid4())
        
        # Generate secret if not provided
        if not request.secret:
            request.secret = str(uuid.uuid4())
        
        # Store webhook configuration
        webhook_config = {
            "webhook_id": webhook_id,
            "user_id": current_user.id,
            "url": str(request.url),
            "events": request.events,
            "secret": request.secret,
            "description": request.description,
            "enabled": request.enabled,
            "retry_count": request.retry_count,
            "retry_delay_seconds": request.retry_delay_seconds,
            "timeout_seconds": request.timeout_seconds,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "total_deliveries": 0,
            "successful_deliveries": 0,
            "failed_deliveries": 0,
            "last_delivery": None,
            "last_error": None
        }
        
        webhook_registry[webhook_id] = webhook_config
        webhook_delivery_log[webhook_id] = []
        
        # Log webhook registration
        audit_logger.log_system_action(
            action="webhook_registered",
            user_id=current_user.id,
            details={
                "webhook_id": webhook_id,
                "url": str(request.url),
                "events": request.events,
                "enabled": request.enabled
            }
        )
        
        logger.info(f"Webhook registered: {webhook_id} for user {current_user.id}")
        
        return WebhookRegistrationResponse(
            webhook_id=webhook_id,
            url=str(request.url),
            events=request.events,
            status="active" if request.enabled else "disabled",
            created_at=webhook_config["created_at"],
            secret=request.secret
        )
        
    except Exception as e:
        logger.error(f"Failed to register webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to register webhook: {str(e)}")


@webhook_router.get("/list", response_model=List[WebhookStatusResponse])
async def list_webhooks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all webhooks for the current user.
    """
    try:
        user_webhooks = []
        
        for webhook_id, config in webhook_registry.items():
            if config["user_id"] == current_user.id:
                # Calculate success rate
                total = config["total_deliveries"]
                successful = config["successful_deliveries"]
                success_rate = (successful / total * 100) if total > 0 else 0.0
                
                user_webhooks.append(WebhookStatusResponse(
                    webhook_id=webhook_id,
                    url=config["url"],
                    events=config["events"],
                    status="active" if config["enabled"] else "disabled",
                    enabled=config["enabled"],
                    total_deliveries=total,
                    successful_deliveries=successful,
                    failed_deliveries=config["failed_deliveries"],
                    success_rate=success_rate,
                    last_delivery=config["last_delivery"],
                    last_error=config["last_error"],
                    created_at=config["created_at"],
                    updated_at=config["updated_at"]
                ))
        
        return user_webhooks
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@webhook_router.get("/{webhook_id}", response_model=WebhookStatusResponse)
async def get_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific webhook.
    """
    try:
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        config = webhook_registry[webhook_id]
        
        # Check ownership
        if config["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate success rate
        total = config["total_deliveries"]
        successful = config["successful_deliveries"]
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return WebhookStatusResponse(
            webhook_id=webhook_id,
            url=config["url"],
            events=config["events"],
            status="active" if config["enabled"] else "disabled",
            enabled=config["enabled"],
            total_deliveries=total,
            successful_deliveries=successful,
            failed_deliveries=config["failed_deliveries"],
            success_rate=success_rate,
            last_delivery=config["last_delivery"],
            last_error=config["last_error"],
            created_at=config["created_at"],
            updated_at=config["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook: {str(e)}")


@webhook_router.put("/{webhook_id}", response_model=WebhookStatusResponse)
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update webhook configuration.
    """
    try:
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        config = webhook_registry[webhook_id]
        
        # Check ownership
        if config["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Update fields
        if request.url is not None:
            config["url"] = str(request.url)
        if request.events is not None:
            config["events"] = request.events
        if request.secret is not None:
            config["secret"] = request.secret
        if request.description is not None:
            config["description"] = request.description
        if request.enabled is not None:
            config["enabled"] = request.enabled
        if request.retry_count is not None:
            config["retry_count"] = request.retry_count
        if request.retry_delay_seconds is not None:
            config["retry_delay_seconds"] = request.retry_delay_seconds
        if request.timeout_seconds is not None:
            config["timeout_seconds"] = request.timeout_seconds
        
        config["updated_at"] = datetime.utcnow()
        
        # Log webhook update
        audit_logger.log_system_action(
            action="webhook_updated",
            user_id=current_user.id,
            details={
                "webhook_id": webhook_id,
                "updated_fields": request.dict(exclude_unset=True)
            }
        )
        
        # Return updated webhook status
        total = config["total_deliveries"]
        successful = config["successful_deliveries"]
        success_rate = (successful / total * 100) if total > 0 else 0.0
        
        return WebhookStatusResponse(
            webhook_id=webhook_id,
            url=config["url"],
            events=config["events"],
            status="active" if config["enabled"] else "disabled",
            enabled=config["enabled"],
            total_deliveries=total,
            successful_deliveries=successful,
            failed_deliveries=config["failed_deliveries"],
            success_rate=success_rate,
            last_delivery=config["last_delivery"],
            last_error=config["last_error"],
            created_at=config["created_at"],
            updated_at=config["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update webhook: {str(e)}")


@webhook_router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a webhook.
    """
    try:
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        config = webhook_registry[webhook_id]
        
        # Check ownership
        if config["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Remove webhook
        del webhook_registry[webhook_id]
        if webhook_id in webhook_delivery_log:
            del webhook_delivery_log[webhook_id]
        
        # Log webhook deletion
        audit_logger.log_system_action(
            action="webhook_deleted",
            user_id=current_user.id,
            details={
                "webhook_id": webhook_id,
                "url": config["url"]
            }
        )
        
        logger.info(f"Webhook deleted: {webhook_id} by user {current_user.id}")
        
        return {"message": "Webhook deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete webhook: {str(e)}")


@webhook_router.get("/{webhook_id}/deliveries", response_model=List[WebhookDeliveryAttempt])
async def get_webhook_deliveries(
    webhook_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get delivery history for a webhook.
    """
    try:
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        config = webhook_registry[webhook_id]
        
        # Check ownership
        if config["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get delivery history
        deliveries = webhook_delivery_log.get(webhook_id, [])
        deliveries = sorted(deliveries, key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        deliveries = deliveries[offset:offset + limit]
        
        return [
            WebhookDeliveryAttempt(
                attempt_id=delivery["attempt_id"],
                webhook_id=delivery["webhook_id"],
                event_type=delivery["event_type"],
                event_id=delivery["event_id"],
                status=delivery["status"],
                response_code=delivery.get("response_code"),
                response_body=delivery.get("response_body"),
                error_message=delivery.get("error_message"),
                attempt_number=delivery["attempt_number"],
                created_at=delivery["created_at"],
                completed_at=delivery.get("completed_at")
            )
            for delivery in deliveries
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get webhook deliveries {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get webhook deliveries: {str(e)}")


@webhook_router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test webhook to verify configuration.
    """
    try:
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        config = webhook_registry[webhook_id]
        
        # Check ownership
        if config["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create test event
        test_event = {
            "event_type": "webhook.test",
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "message": "This is a test webhook from HealthMate",
                "user_id": current_user.id,
                "webhook_id": webhook_id
            },
            "source": "healthmate"
        }
        
        # Send test webhook
        success = await _deliver_webhook(webhook_id, test_event)
        
        if success:
            return {"message": "Test webhook sent successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to send test webhook")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test webhook {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test webhook: {str(e)}")


@webhook_router.post("/{webhook_id}/retry-failed")
async def retry_failed_deliveries(
    webhook_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retry failed webhook deliveries.
    """
    try:
        if webhook_id not in webhook_registry:
            raise HTTPException(status_code=404, detail="Webhook not found")
        
        config = webhook_registry[webhook_id]
        
        # Check ownership
        if config["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get failed deliveries
        deliveries = webhook_delivery_log.get(webhook_id, [])
        failed_deliveries = [
            delivery for delivery in deliveries 
            if delivery["status"] == "failed" and delivery["attempt_number"] < config["retry_count"]
        ]
        
        if not failed_deliveries:
            return {"message": "No failed deliveries to retry"}
        
        # Retry failed deliveries in background
        background_tasks.add_task(_retry_failed_deliveries, webhook_id, failed_deliveries)
        
        return {
            "message": f"Retrying {len(failed_deliveries)} failed deliveries",
            "deliveries_count": len(failed_deliveries)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry webhook deliveries {webhook_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retry webhook deliveries: {str(e)}")


# Webhook delivery functions
async def _deliver_webhook(webhook_id: str, event_data: Dict[str, Any]) -> bool:
    """Deliver webhook to registered endpoint."""
    if webhook_id not in webhook_registry:
        logger.error(f"Webhook {webhook_id} not found")
        return False
    
    config = webhook_registry[webhook_id]
    
    if not config["enabled"]:
        logger.info(f"Webhook {webhook_id} is disabled")
        return False
    
    # Check if event type is subscribed
    if event_data["event_type"] not in config["events"]:
        logger.info(f"Event type {event_data['event_type']} not subscribed for webhook {webhook_id}")
        return False
    
    # Create delivery attempt
    attempt_id = str(uuid.uuid4())
    attempt = {
        "attempt_id": attempt_id,
        "webhook_id": webhook_id,
        "event_type": event_data["event_type"],
        "event_id": event_data["event_id"],
        "status": "pending",
        "attempt_number": 1,
        "created_at": datetime.utcnow(),
        "payload": event_data
    }
    
    webhook_delivery_log[webhook_id].append(attempt)
    
    # Try to deliver
    success = await _attempt_delivery(webhook_id, attempt, config)
    
    # Update webhook statistics
    config["total_deliveries"] += 1
    config["last_delivery"] = datetime.utcnow()
    
    if success:
        config["successful_deliveries"] += 1
    else:
        config["failed_deliveries"] += 1
    
    return success


async def _attempt_delivery(webhook_id: str, attempt: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Attempt to deliver webhook."""
    import aiohttp
    
    try:
        # Prepare payload
        payload = json.dumps(attempt["payload"])
        
        # Add signature if secret is configured
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "HealthMate-Webhook/1.0",
            "X-Webhook-Event": attempt["event_type"],
            "X-Webhook-Event-ID": attempt["event_id"],
            "X-Webhook-Timestamp": attempt["created_at"].isoformat()
        }
        
        if config["secret"]:
            import hmac
            import hashlib
            signature = hmac.new(
                config["secret"].encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        # Make HTTP request
        timeout = aiohttp.ClientTimeout(total=config["timeout_seconds"])
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                config["url"],
                data=payload,
                headers=headers
            ) as response:
                response_body = await response.text()
                
                # Update attempt
                attempt["status"] = "delivered" if response.status < 400 else "failed"
                attempt["response_code"] = response.status
                attempt["response_body"] = response_body
                attempt["completed_at"] = datetime.utcnow()
                
                if response.status >= 400:
                    attempt["error_message"] = f"HTTP {response.status}: {response_body}"
                    logger.warning(f"Webhook delivery failed: {webhook_id} - {response.status}")
                    return False
                
                logger.info(f"Webhook delivered successfully: {webhook_id}")
                return True
                
    except Exception as e:
        # Update attempt with error
        attempt["status"] = "failed"
        attempt["error_message"] = str(e)
        attempt["completed_at"] = datetime.utcnow()
        
        logger.error(f"Webhook delivery error: {webhook_id} - {e}")
        return False


async def _retry_failed_deliveries(webhook_id: str, failed_deliveries: List[Dict[str, Any]]) -> None:
    """Retry failed webhook deliveries."""
    if webhook_id not in webhook_registry:
        return
    
    config = webhook_registry[webhook_id]
    
    for delivery in failed_deliveries:
        # Create new attempt
        attempt_id = str(uuid.uuid4())
        attempt = {
            "attempt_id": attempt_id,
            "webhook_id": webhook_id,
            "event_type": delivery["event_type"],
            "event_id": delivery["event_id"],
            "status": "pending",
            "attempt_number": delivery["attempt_number"] + 1,
            "created_at": datetime.utcnow(),
            "payload": delivery["payload"]
        }
        
        webhook_delivery_log[webhook_id].append(attempt)
        
        # Wait before retry
        await asyncio.sleep(config["retry_delay_seconds"])
        
        # Attempt delivery
        success = await _attempt_delivery(webhook_id, attempt, config)
        
        if success:
            logger.info(f"Webhook retry successful: {webhook_id}")
        else:
            logger.warning(f"Webhook retry failed: {webhook_id}")


# Webhook event dispatcher
async def dispatch_webhook_event(event_type: str, event_data: Dict[str, Any], user_id: int) -> None:
    """Dispatch webhook event to all registered endpoints."""
    # Find webhooks for this user and event type
    matching_webhooks = []
    
    for webhook_id, config in webhook_registry.items():
        if (config["user_id"] == user_id and 
            config["enabled"] and 
            event_type in config["events"]):
            matching_webhooks.append(webhook_id)
    
    if not matching_webhooks:
        return
    
    # Create event
    event = {
        "event_type": event_type,
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "data": event_data,
        "source": "healthmate"
    }
    
    # Deliver to all matching webhooks
    for webhook_id in matching_webhooks:
        await _deliver_webhook(webhook_id, event) 