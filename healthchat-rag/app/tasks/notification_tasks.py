"""
Notification background tasks for HealthMate.

This module provides background tasks for:
- Notification delivery
- Alert processing
- Email and SMS sending
- Push notification management
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.utils.performance_monitoring import monitor_custom_performance

logger = logging.getLogger(__name__)

@celery_app.task
@monitor_custom_performance("process_notification_queue")
def process_notification_queue():
    """
    Process the notification queue and send pending notifications.
    
    This task runs every minute to process queued notifications
    and deliver them to users.
    """
    try:
        db = SessionLocal()
        
        # Get pending notifications (in a real implementation, this would query a notification table)
        pending_notifications = get_pending_notifications(db)
        
        sent_count = 0
        error_count = 0
        
        for notification in pending_notifications:
            try:
                # Send notification based on type
                if notification["type"] == "email":
                    result = send_email_notification(notification)
                elif notification["type"] == "sms":
                    result = send_sms_notification(notification)
                elif notification["type"] == "push":
                    result = send_push_notification(notification)
                else:
                    logger.warning(f"Unknown notification type: {notification['type']}")
                    continue
                
                if result["success"]:
                    sent_count += 1
                    mark_notification_sent(notification["id"], db)
                else:
                    error_count += 1
                    mark_notification_failed(notification["id"], db, result["error"])
                    
            except Exception as e:
                logger.error(f"Failed to send notification {notification['id']}: {e}")
                error_count += 1
                mark_notification_failed(notification["id"], db, str(e))
        
        logger.info(f"Notification queue processed: {sent_count} sent, {error_count} errors")
        
        return {
            "status": "completed",
            "sent_count": sent_count,
            "error_count": error_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Notification queue processing failed: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("send_health_alert")
def send_health_alert(user_id: int, alert_type: str, alert_data: Dict[str, Any]):
    """
    Send health alert to a specific user.
    
    Args:
        user_id: ID of the user to send alert to
        alert_type: Type of health alert
        alert_data: Alert data and context
    """
    try:
        db = SessionLocal()
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Create notification based on alert type
        notification = create_health_alert_notification(user, alert_type, alert_data)
        
        # Send notification
        if notification["preferred_channel"] == "email":
            result = send_email_notification(notification)
        elif notification["preferred_channel"] == "sms":
            result = send_sms_notification(notification)
        else:
            result = send_push_notification(notification)
        
        # Log the alert
        log_health_alert(user_id, alert_type, alert_data, result, db)
        
        logger.info(f"Health alert sent to user {user_id}: {alert_type}")
        
        return {
            "user_id": user_id,
            "alert_type": alert_type,
            "success": result["success"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health alert failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("send_medication_reminder")
def send_medication_reminder(user_id: int, medication_name: str, dosage: str, time: str):
    """
    Send medication reminder to a user.
    
    Args:
        user_id: ID of the user to send reminder to
        medication_name: Name of the medication
        dosage: Dosage information
        time: Time to take medication
    """
    try:
        db = SessionLocal()
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Create medication reminder notification
        notification = create_medication_reminder_notification(user, medication_name, dosage, time)
        
        # Send notification
        result = send_notification(notification)
        
        # Log the reminder
        log_medication_reminder(user_id, medication_name, dosage, time, result, db)
        
        logger.info(f"Medication reminder sent to user {user_id}: {medication_name}")
        
        return {
            "user_id": user_id,
            "medication_name": medication_name,
            "success": result["success"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Medication reminder failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("send_appointment_reminder")
def send_appointment_reminder(user_id: int, appointment_data: Dict[str, Any]):
    """
    Send appointment reminder to a user.
    
    Args:
        user_id: ID of the user to send reminder to
        appointment_data: Appointment information
    """
    try:
        db = SessionLocal()
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Create appointment reminder notification
        notification = create_appointment_reminder_notification(user, appointment_data)
        
        # Send notification
        result = send_notification(notification)
        
        # Log the reminder
        log_appointment_reminder(user_id, appointment_data, result, db)
        
        logger.info(f"Appointment reminder sent to user {user_id}")
        
        return {
            "user_id": user_id,
            "appointment_id": appointment_data.get("id"),
            "success": result["success"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Appointment reminder failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("send_health_summary")
def send_health_summary(user_id: int, summary_type: str = "weekly"):
    """
    Send health summary to a user.
    
    Args:
        user_id: ID of the user to send summary to
        summary_type: Type of summary (daily, weekly, monthly)
    """
    try:
        db = SessionLocal()
        
        # Get user information
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Generate health summary
        summary_data = generate_health_summary(user_id, summary_type, db)
        
        # Create summary notification
        notification = create_health_summary_notification(user, summary_data, summary_type)
        
        # Send notification
        result = send_notification(notification)
        
        # Log the summary
        log_health_summary(user_id, summary_type, result, db)
        
        logger.info(f"Health summary sent to user {user_id}: {summary_type}")
        
        return {
            "user_id": user_id,
            "summary_type": summary_type,
            "success": result["success"],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health summary failed for user {user_id}: {e}")
        raise
    finally:
        db.close()

@celery_app.task
@monitor_custom_performance("cleanup_old_notifications")
def cleanup_old_notifications(days: int = 30):
    """
    Clean up old notifications from the database.
    
    Args:
        days: Number of days to keep notifications (default: 30)
    """
    try:
        db = SessionLocal()
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Delete old notifications (in a real implementation, this would query a notification table)
        deleted_count = cleanup_notifications_before(cutoff_date, db)
        
        logger.info(f"Cleaned up {deleted_count} old notifications")
        
        return {
            "deleted_count": deleted_count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Notification cleanup failed: {e}")
        raise
    finally:
        db.close()

# Helper functions

def get_pending_notifications(db) -> List[Dict[str, Any]]:
    """Get pending notifications from the database."""
    # This would query a real notification table
    # For now, return mock data
    return [
        {
            "id": 1,
            "user_id": 1,
            "type": "email",
            "subject": "Health Alert",
            "message": "Your blood pressure reading is high",
            "preferred_channel": "email",
            "created_at": datetime.now() - timedelta(minutes=5)
        }
    ]

def send_email_notification(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send email notification."""
    try:
        # This would use a real email service (SendGrid, AWS SES, etc.)
        # For now, just log the email
        logger.info(f"Email sent to {notification.get('user_email', 'unknown')}: {notification.get('subject', 'No subject')}")
        
        return {
            "success": True,
            "channel": "email",
            "message_id": f"email_{datetime.now().timestamp()}"
        }
        
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        return {
            "success": False,
            "channel": "email",
            "error": str(e)
        }

def send_sms_notification(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send SMS notification."""
    try:
        # This would use a real SMS service (Twilio, AWS SNS, etc.)
        # For now, just log the SMS
        logger.info(f"SMS sent to {notification.get('user_phone', 'unknown')}: {notification.get('message', 'No message')}")
        
        return {
            "success": True,
            "channel": "sms",
            "message_id": f"sms_{datetime.now().timestamp()}"
        }
        
    except Exception as e:
        logger.error(f"SMS notification failed: {e}")
        return {
            "success": False,
            "channel": "sms",
            "error": str(e)
        }

def send_push_notification(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send push notification."""
    try:
        # This would use a real push notification service (FCM, APNS, etc.)
        # For now, just log the push notification
        logger.info(f"Push notification sent to {notification.get('user_id', 'unknown')}: {notification.get('title', 'No title')}")
        
        return {
            "success": True,
            "channel": "push",
            "message_id": f"push_{datetime.now().timestamp()}"
        }
        
    except Exception as e:
        logger.error(f"Push notification failed: {e}")
        return {
            "success": False,
            "channel": "push",
            "error": str(e)
        }

def send_notification(notification: Dict[str, Any]) -> Dict[str, Any]:
    """Send notification through preferred channel."""
    channel = notification.get("preferred_channel", "email")
    
    if channel == "email":
        return send_email_notification(notification)
    elif channel == "sms":
        return send_sms_notification(notification)
    elif channel == "push":
        return send_push_notification(notification)
    else:
        return send_email_notification(notification)  # Default to email

def create_health_alert_notification(user: User, alert_type: str, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create health alert notification."""
    return {
        "user_id": user.id,
        "user_email": user.email,
        "user_phone": getattr(user, 'phone', None),
        "type": "health_alert",
        "preferred_channel": "email",  # Could be user preference
        "subject": f"Health Alert: {alert_type}",
        "title": f"Health Alert: {alert_type}",
        "message": f"Your health data indicates {alert_type}. Please review your recent readings.",
        "alert_data": alert_data,
        "priority": "high"
    }

def create_medication_reminder_notification(user: User, medication_name: str, dosage: str, time: str) -> Dict[str, Any]:
    """Create medication reminder notification."""
    return {
        "user_id": user.id,
        "user_email": user.email,
        "user_phone": getattr(user, 'phone', None),
        "type": "medication_reminder",
        "preferred_channel": "sms",  # SMS is often preferred for medication reminders
        "subject": f"Medication Reminder: {medication_name}",
        "title": f"Time to take {medication_name}",
        "message": f"Please take {dosage} of {medication_name} at {time}",
        "medication_name": medication_name,
        "dosage": dosage,
        "time": time,
        "priority": "medium"
    }

def create_appointment_reminder_notification(user: User, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create appointment reminder notification."""
    return {
        "user_id": user.id,
        "user_email": user.email,
        "user_phone": getattr(user, 'phone', None),
        "type": "appointment_reminder",
        "preferred_channel": "email",
        "subject": f"Appointment Reminder: {appointment_data.get('type', 'Medical')}",
        "title": f"Appointment Reminder",
        "message": f"Your {appointment_data.get('type', 'medical')} appointment is scheduled for {appointment_data.get('datetime', 'unknown time')}",
        "appointment_data": appointment_data,
        "priority": "medium"
    }

def create_health_summary_notification(user: User, summary_data: Dict[str, Any], summary_type: str) -> Dict[str, Any]:
    """Create health summary notification."""
    return {
        "user_id": user.id,
        "user_email": user.email,
        "user_phone": getattr(user, 'phone', None),
        "type": "health_summary",
        "preferred_channel": "email",
        "subject": f"Your {summary_type.capitalize()} Health Summary",
        "title": f"{summary_type.capitalize()} Health Summary",
        "message": f"Here's your {summary_type} health summary. Your overall health score is {summary_data.get('health_score', 'N/A')}",
        "summary_data": summary_data,
        "summary_type": summary_type,
        "priority": "low"
    }

def generate_health_summary(user_id: int, summary_type: str, db) -> Dict[str, Any]:
    """Generate health summary for a user."""
    # This would query actual health data and generate a summary
    # For now, return mock data
    return {
        "health_score": 85,
        "metrics_tracked": 5,
        "data_points": 150,
        "trends": "improving",
        "recommendations": ["Continue regular exercise", "Monitor blood pressure"]
    }

def mark_notification_sent(notification_id: int, db):
    """Mark notification as sent in database."""
    # This would update a real notification table
    logger.info(f"Marked notification {notification_id} as sent")

def mark_notification_failed(notification_id: int, db, error: str):
    """Mark notification as failed in database."""
    # This would update a real notification table
    logger.error(f"Marked notification {notification_id} as failed: {error}")

def cleanup_notifications_before(cutoff_date: datetime, db) -> int:
    """Clean up notifications older than cutoff date."""
    # This would delete from a real notification table
    # For now, return mock count
    return 25

def log_health_alert(user_id: int, alert_type: str, alert_data: Dict[str, Any], result: Dict[str, Any], db):
    """Log health alert in database."""
    # This would insert into a real alert log table
    logger.info(f"Logged health alert for user {user_id}: {alert_type}")

def log_medication_reminder(user_id: int, medication_name: str, dosage: str, time: str, result: Dict[str, Any], db):
    """Log medication reminder in database."""
    # This would insert into a real reminder log table
    logger.info(f"Logged medication reminder for user {user_id}: {medication_name}")

def log_appointment_reminder(user_id: int, appointment_data: Dict[str, Any], result: Dict[str, Any], db):
    """Log appointment reminder in database."""
    # This would insert into a real reminder log table
    logger.info(f"Logged appointment reminder for user {user_id}")

def log_health_summary(user_id: int, summary_type: str, result: Dict[str, Any], db):
    """Log health summary in database."""
    # This would insert into a real summary log table
    logger.info(f"Logged health summary for user {user_id}: {summary_type}") 