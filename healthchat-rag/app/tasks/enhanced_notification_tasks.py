"""
Enhanced Notification Tasks for HealthMate

This module provides Celery tasks for:
- Automated health metric monitoring and alerting
- Smart medication reminder processing
- Emergency health condition monitoring
- Contextual notification generation
- Notification preference management
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from celery import current_task

from app.celery_app import celery_app
from app.database import SessionLocal
from app.config import Settings
from app.models.user import User
from app.models.health_data import HealthData
from app.models.enhanced_health_models import (
    UserHealthProfile, EnhancedMedication, MedicationDoseLog,
    HealthMetricsAggregation, EnhancedSymptomLog
)
from app.services.enhanced_notification_service import EnhancedNotificationService
from app.utils.performance_monitoring import monitor_custom_performance
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)
audit_logger = AuditLogger()


def run_async(coro):
    """Helper function to run async coroutines in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task
@monitor_custom_performance("monitor_health_metrics_for_all_users")
def monitor_health_metrics_for_all_users():
    """
    Monitor health metrics for all active users and send alerts for threshold violations.
    
    This task runs periodically to check all users' health data and generate
    appropriate notifications based on smart notification logic.
    """
    try:
        db = SessionLocal()
        settings = Settings()
        enhanced_service = EnhancedNotificationService(settings)
        
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        total_alerts = 0
        successful_users = 0
        failed_users = 0
        
        for user in active_users:
            try:
                # Monitor health metrics for this user
                alerts = run_async(enhanced_service.monitor_health_metrics_and_alert(user.id, db))
                total_alerts += len(alerts)
                successful_users += 1
                
                logger.info(f"Health metrics monitored for user {user.id}: {len(alerts)} alerts generated")
                
            except Exception as e:
                logger.error(f"Failed to monitor health metrics for user {user.id}: {e}")
                failed_users += 1
        
        # Log task completion
        audit_logger.log_system_action(
            action="health_metrics_monitoring_completed",
            details={
                "total_users": len(active_users),
                "successful_users": successful_users,
                "failed_users": failed_users,
                "total_alerts": total_alerts,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Health metrics monitoring completed: {successful_users} users processed, {total_alerts} alerts generated")
        
        return {
            "status": "completed",
            "total_users": len(active_users),
            "successful_users": successful_users,
            "failed_users": failed_users,
            "total_alerts": total_alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health metrics monitoring task failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("process_medication_reminders_for_all_users")
def process_medication_reminders_for_all_users():
    """
    Process medication reminders for all active users.
    
    This task runs periodically to check for missed doses and upcoming
    medication schedules, sending appropriate reminders.
    """
    try:
        db = SessionLocal()
        settings = Settings()
        enhanced_service = EnhancedNotificationService(settings)
        
        # Get all active users with medications
        users_with_medications = db.query(User).join(
            EnhancedMedication, User.id == EnhancedMedication.user_id
        ).filter(
            and_(
                User.is_active == True,
                EnhancedMedication.status == "active"
            )
        ).distinct().all()
        
        total_reminders = 0
        successful_users = 0
        failed_users = 0
        
        for user in users_with_medications:
            try:
                # Process medication reminders for this user
                reminders = run_async(enhanced_service.process_medication_reminders(user.id, db))
                total_reminders += len(reminders)
                successful_users += 1
                
                logger.info(f"Medication reminders processed for user {user.id}: {len(reminders)} reminders sent")
                
            except Exception as e:
                logger.error(f"Failed to process medication reminders for user {user.id}: {e}")
                failed_users += 1
        
        # Log task completion
        audit_logger.log_system_action(
            action="medication_reminders_processing_completed",
            details={
                "total_users": len(users_with_medications),
                "successful_users": successful_users,
                "failed_users": failed_users,
                "total_reminders": total_reminders,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Medication reminders processing completed: {successful_users} users processed, {total_reminders} reminders sent")
        
        return {
            "status": "completed",
            "total_users": len(users_with_medications),
            "successful_users": successful_users,
            "failed_users": failed_users,
            "total_reminders": total_reminders,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Medication reminders processing task failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("check_emergency_conditions_for_all_users")
def check_emergency_conditions_for_all_users():
    """
    Check for emergency health conditions for all active users.
    
    This task runs frequently to monitor for critical health values
    that require immediate attention and emergency notifications.
    """
    try:
        db = SessionLocal()
        settings = Settings()
        enhanced_service = EnhancedNotificationService(settings)
        
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        total_emergencies = 0
        successful_users = 0
        failed_users = 0
        
        for user in active_users:
            try:
                # Check emergency conditions for this user
                emergencies = run_async(enhanced_service.check_emergency_conditions(user.id, db))
                total_emergencies += len(emergencies)
                successful_users += 1
                
                if emergencies:
                    logger.warning(f"Emergency conditions detected for user {user.id}: {len(emergencies)} emergencies")
                else:
                    logger.info(f"Emergency conditions checked for user {user.id}: no emergencies detected")
                
            except Exception as e:
                logger.error(f"Failed to check emergency conditions for user {user.id}: {e}")
                failed_users += 1
        
        # Log task completion
        audit_logger.log_system_action(
            action="emergency_conditions_check_completed",
            details={
                "total_users": len(active_users),
                "successful_users": successful_users,
                "failed_users": failed_users,
                "total_emergencies": total_emergencies,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Emergency conditions check completed: {successful_users} users processed, {total_emergencies} emergencies detected")
        
        return {
            "status": "completed",
            "total_users": len(active_users),
            "successful_users": successful_users,
            "failed_users": failed_users,
            "total_emergencies": total_emergencies,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Emergency conditions check task failed: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("send_contextual_notifications")
def send_contextual_notifications(
    user_id: int,
    context: str,
    context_data: Dict[str, Any]
):
    """
    Send contextual notifications based on specific triggers.
    
    Args:
        user_id: Target user ID
        context: Context type (health_metric, medication, appointment, etc.)
        context_data: Context-specific data
    """
    try:
        db = SessionLocal()
        settings = Settings()
        enhanced_service = EnhancedNotificationService(settings)
        
        # Send contextual notification
        result = run_async(enhanced_service.send_contextual_notification(
            user_id=user_id,
            context=context,
            context_data=context_data,
            db=db
        ))
        
        logger.info(f"Contextual notification sent for user {user_id}, context: {context}")
        
        return {
            "user_id": user_id,
            "context": context,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send contextual notification for user {user_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("send_smart_notification")
def send_smart_notification(
    user_id: int,
    notification_type: str,
    title: str,
    message: str,
    context_data: Optional[Dict[str, Any]] = None
):
    """
    Send a smart notification using intelligent targeting and prioritization.
    
    Args:
        user_id: Target user ID
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        context_data: Additional context data
    """
    try:
        db = SessionLocal()
        settings = Settings()
        enhanced_service = EnhancedNotificationService(settings)
        
        # Convert string to enum
        from app.models.notification_models import NotificationType
        notification_type_enum = NotificationType(notification_type)
        
        # Send smart notification
        result = run_async(enhanced_service.send_smart_notification(
            user_id=user_id,
            notification_type=notification_type_enum,
            title=title,
            message=message,
            context_data=context_data,
            db=db
        ))
        
        logger.info(f"Smart notification sent for user {user_id}, type: {notification_type}")
        
        return {
            "user_id": user_id,
            "notification_type": notification_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to send smart notification for user {user_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("process_health_data_alerts")
def process_health_data_alerts(user_id: int, health_data_id: int):
    """
    Process health data alerts for a specific user and health data point.
    
    Args:
        user_id: Target user ID
        health_data_id: Health data record ID
    """
    try:
        db = SessionLocal()
        settings = Settings()
        enhanced_service = EnhancedNotificationService(settings)
        
        # Get health data
        health_data = db.query(HealthData).filter(
            and_(
                HealthData.id == health_data_id,
                HealthData.user_id == user_id
            )
        ).first()
        
        if not health_data:
            logger.warning(f"Health data not found: {health_data_id} for user {user_id}")
            return {
                "user_id": user_id,
                "health_data_id": health_data_id,
                "status": "not_found",
                "timestamp": datetime.now().isoformat()
            }
        
        # Monitor health metrics for this specific data point
        alerts = run_async(enhanced_service.monitor_health_metrics_and_alert(user_id, db))
        
        logger.info(f"Health data alerts processed for user {user_id}, data {health_data_id}: {len(alerts)} alerts generated")
        
        return {
            "user_id": user_id,
            "health_data_id": health_data_id,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to process health data alerts for user {user_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("update_user_notification_preferences")
def update_user_notification_preferences(
    user_id: int,
    preferences: Dict[str, Any]
):
    """
    Update user notification preferences.
    
    Args:
        user_id: Target user ID
        preferences: New notification preferences
    """
    try:
        db = SessionLocal()
        
        # Get user notification preferences
        from app.models.notification_models import UserNotificationPreference
        
        user_prefs = db.query(UserNotificationPreference).filter(
            UserNotificationPreference.user_id == user_id
        ).first()
        
        if not user_prefs:
            # Create new preferences
            user_prefs = UserNotificationPreference(
                user_id=user_id,
                **preferences
            )
            db.add(user_prefs)
        else:
            # Update existing preferences
            for key, value in preferences.items():
                if hasattr(user_prefs, key):
                    setattr(user_prefs, key, value)
        
        db.commit()
        
        logger.info(f"Notification preferences updated for user {user_id}")
        
        return {
            "user_id": user_id,
            "preferences": user_prefs.to_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to update notification preferences for user {user_id}: {e}")
        raise
    finally:
        db.close()


@celery_app.task
@monitor_custom_performance("cleanup_old_notifications")
def cleanup_old_notifications(days_to_keep: int = 90):
    """
    Clean up old notifications to maintain database performance.
    
    Args:
        days_to_keep: Number of days to keep notifications
    """
    try:
        db = SessionLocal()
        
        from app.models.notification_models import Notification, NotificationDeliveryAttempt
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Delete old notifications
        old_notifications = db.query(Notification).filter(
            Notification.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for notification in old_notifications:
            db.delete(notification)
            deleted_count += 1
        
        # Delete old delivery attempts
        old_attempts = db.query(NotificationDeliveryAttempt).filter(
            NotificationDeliveryAttempt.attempted_at < cutoff_date
        ).all()
        
        deleted_attempts = 0
        for attempt in old_attempts:
            db.delete(attempt)
            deleted_attempts += 1
        
        db.commit()
        
        logger.info(f"Cleanup completed: {deleted_count} notifications, {deleted_attempts} delivery attempts deleted")
        
        return {
            "deleted_notifications": deleted_count,
            "deleted_delivery_attempts": deleted_attempts,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old notifications: {e}")
        raise
    finally:
        db.close()


# Import required for the tasks
from sqlalchemy import and_ 