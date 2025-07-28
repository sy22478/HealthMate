"""
Enhanced Notification Service for HealthMate

This module provides:
- Integration of smart notification logic with existing notification system
- Automated health metric monitoring and alerting
- Medication reminder scheduling and management
- Emergency health alert system
- Contextual notification generation
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config import Settings
from app.models.notification_models import (
    Notification, NotificationTemplate, NotificationDeliveryAttempt,
    NotificationStatus, NotificationChannel, NotificationType, NotificationPriority,
    UserNotificationPreference
)
from app.models.user import User
from app.models.health_data import HealthData
from app.models.enhanced_health_models import (
    UserHealthProfile, EnhancedMedication, MedicationDoseLog, 
    HealthMetricsAggregation, EnhancedSymptomLog
)
from app.exceptions.notification_exceptions import NotificationError
from app.services.notification_service import NotificationService
from app.services.smart_notification_logic import SmartNotificationLogic, NotificationUrgency
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class EnhancedNotificationService:
    """Enhanced notification service with smart logic integration."""
    
    def __init__(self, settings: Settings):
        """Initialize the enhanced notification service."""
        self.settings = settings
        self.notification_service = NotificationService(settings)
        self.smart_logic = SmartNotificationLogic(settings)
        self.audit_logger = AuditLogger()
        
        logger.info("Enhanced notification service initialized")
    
    async def send_smart_notification(
        self,
        user_id: int,
        notification_type: NotificationType,
        title: str,
        message: str,
        context_data: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Send a notification using smart logic for targeting and prioritization.
        
        Args:
            user_id: Target user ID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            context_data: Additional context data
            db: Database session
            
        Returns:
            Dictionary with delivery results
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotificationError(f"User not found: {user_id}")
            
            # Classify notification urgency
            urgency = self.smart_logic.classify_notification_urgency(
                notification_type, context_data, user
            )
            
            # Check if notification should be sent
            should_send, reason = self.smart_logic.should_send_notification(
                user, notification_type, urgency, context_data, db
            )
            
            if not should_send:
                logger.info(f"Notification not sent for user {user_id}: {reason}")
                return {
                    "notification_id": None,
                    "user_id": user_id,
                    "sent": False,
                    "reason": reason,
                    "urgency": urgency.value
                }
            
            # Get optimal send time
            optimal_time = self.smart_logic.get_optimal_send_time(
                user, notification_type, urgency
            )
            
            # Determine priority based on urgency
            priority = self._urgency_to_priority(urgency)
            
            # Get optimal channels based on urgency
            channels = self.smart_logic.get_notification_channels_by_urgency(
                user, urgency, notification_type
            )
            
            # Add context data to template data
            template_data = context_data or {}
            template_data.update({
                "urgency": urgency.value,
                "optimal_send_time": optimal_time.isoformat(),
                "context": "smart_notification"
            })
            
            # Send notification
            result = await self.notification_service.send_notification(
                user_id=user_id,
                notification_type=notification_type,
                title=title,
                message=message,
                priority=priority,
                channels=channels,
                strategy=self.notification_service.NotificationStrategy.SMART_ROUTING,
                template_data=template_data,
                scheduled_time=optimal_time if optimal_time > datetime.now() else None,
                db=db
            )
            
            # Log smart notification
            self.audit_logger.log_system_action(
                action="smart_notification_sent",
                details={
                    "user_id": user_id,
                    "notification_id": result.get("notification_id"),
                    "type": notification_type.value,
                    "urgency": urgency.value,
                    "priority": priority.value,
                    "channels": [c.value for c in channels],
                    "optimal_time": optimal_time.isoformat(),
                    "reason": reason
                }
            )
            
            return {
                **result,
                "urgency": urgency.value,
                "optimal_time": optimal_time.isoformat(),
                "reason": reason
            }
            
        except Exception as e:
            logger.error(f"Failed to send smart notification to user {user_id}: {e}")
            raise NotificationError(f"Failed to send smart notification: {e}")
    
    def _urgency_to_priority(self, urgency: NotificationUrgency) -> NotificationPriority:
        """Convert urgency to notification priority."""
        urgency_priority_map = {
            NotificationUrgency.LOW: NotificationPriority.LOW,
            NotificationUrgency.MEDIUM: NotificationPriority.NORMAL,
            NotificationUrgency.HIGH: NotificationPriority.HIGH,
            NotificationUrgency.CRITICAL: NotificationPriority.URGENT,
            NotificationUrgency.EMERGENCY: NotificationPriority.EMERGENCY
        }
        return urgency_priority_map.get(urgency, NotificationPriority.NORMAL)
    
    async def monitor_health_metrics_and_alert(
        self,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Monitor user's health metrics and generate alerts for threshold violations.
        
        Args:
            user_id: Target user ID
            db: Database session
            
        Returns:
            List of generated alerts
        """
        alerts = []
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotificationError(f"User not found: {user_id}")
            
            # Get recent health data
            recent_data = db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user_id,
                    HealthData.timestamp >= datetime.now() - timedelta(hours=24)
                )
            ).all()
            
            for data_point in recent_data:
                try:
                    # Parse metric value
                    if data_point.data_type == "blood_pressure":
                        if isinstance(data_point.value, dict):
                            systolic = float(data_point.value.get("systolic", 0))
                            diastolic = float(data_point.value.get("diastolic", 0))
                            
                            # Check systolic pressure
                            systolic_alerts = self.smart_logic.check_health_metric_thresholds(
                                user, "blood_pressure_systolic", systolic, db
                            )
                            
                            # Check diastolic pressure
                            diastolic_alerts = self.smart_logic.check_health_metric_thresholds(
                                user, "blood_pressure_diastolic", diastolic, db
                            )
                            
                            alerts.extend(systolic_alerts)
                            alerts.extend(diastolic_alerts)
                    
                    elif data_point.data_type in ["heart_rate", "blood_glucose", "temperature", "oxygen_saturation"]:
                        metric_value = float(data_point.value)
                        metric_alerts = self.smart_logic.check_health_metric_thresholds(
                            user, data_point.data_type, metric_value, db
                        )
                        alerts.extend(metric_alerts)
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error parsing health data for user {user_id}: {e}")
                    continue
            
            # Send alerts
            sent_alerts = []
            for alert in alerts:
                try:
                    result = await self.send_smart_notification(
                        user_id=user_id,
                        notification_type=alert["notification_type"],
                        title=f"Health Alert: {alert['description']}",
                        message=f"Your {alert['description'].lower()} is {alert['value']} {alert['unit']}. "
                               f"This is outside the normal range of {alert.get('threshold', 'N/A')} {alert['unit']}. "
                               f"Please consult with your healthcare provider if this persists.",
                        context_data={
                            "alert_type": alert["type"],
                            "metric": alert["metric"],
                            "value": alert["value"],
                            "threshold": alert.get("threshold"),
                            "unit": alert["unit"],
                            "urgency": alert["urgency"].value,
                            "trigger_type": "health_metric_threshold"
                        },
                        db=db
                    )
                    
                    sent_alerts.append({
                        "alert": alert,
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to send health alert for user {user_id}: {e}")
            
            return sent_alerts
            
        except Exception as e:
            logger.error(f"Failed to monitor health metrics for user {user_id}: {e}")
            return alerts
    
    async def process_medication_reminders(
        self,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Process medication reminders for a user.
        
        Args:
            user_id: Target user ID
            db: Database session
            
        Returns:
            List of sent medication reminders
        """
        reminders = []
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotificationError(f"User not found: {user_id}")
            
            # Check for medication reminders
            medication_alerts = self.smart_logic.check_medication_reminders(user, db)
            
            # Send reminders
            for alert in medication_alerts:
                try:
                    if alert["type"] == "missed_dose":
                        title = f"Missed Medication: {alert['medication_name']}"
                        message = (f"You missed your scheduled dose of {alert['medication_name']} at {alert['scheduled_time'].strftime('%I:%M %p')}. "
                                  f"Please take it as soon as possible and contact your healthcare provider if you have concerns.")
                    else:
                        title = f"Medication Reminder: {alert['medication_name']}"
                        message = (f"Your dose of {alert['medication_name']} is due at {alert['scheduled_time'].strftime('%I:%M %p')}. "
                                  f"Please take your medication as prescribed.")
                    
                    result = await self.send_smart_notification(
                        user_id=user_id,
                        notification_type=alert["notification_type"],
                        title=title,
                        message=message,
                        context_data={
                            "alert_type": alert["type"],
                            "medication_id": alert["medication_id"],
                            "medication_name": alert["medication_name"],
                            "scheduled_time": alert["scheduled_time"].isoformat(),
                            "urgency": alert["urgency"].value,
                            "trigger_type": "medication_reminder"
                        },
                        db=db
                    )
                    
                    reminders.append({
                        "alert": alert,
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to send medication reminder for user {user_id}: {e}")
            
            return reminders
            
        except Exception as e:
            logger.error(f"Failed to process medication reminders for user {user_id}: {e}")
            return reminders
    
    async def check_emergency_conditions(
        self,
        user_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Check for emergency health conditions and send immediate alerts.
        
        Args:
            user_id: Target user ID
            db: Database session
            
        Returns:
            List of emergency alerts sent
        """
        emergency_alerts = []
        
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotificationError(f"User not found: {user_id}")
            
            # Check for emergency conditions
            emergencies = self.smart_logic.check_emergency_conditions(user, db)
            
            # Send emergency alerts
            for emergency in emergencies:
                try:
                    result = await self.send_smart_notification(
                        user_id=user_id,
                        notification_type=emergency["notification_type"],
                        title=f"EMERGENCY: {emergency['description']}",
                        message=f"🚨 EMERGENCY ALERT: {emergency['description']}. "
                               f"Current value: {emergency['value']}. "
                               f"This requires immediate medical attention. "
                               f"Please contact emergency services or your healthcare provider immediately.",
                        context_data={
                            "alert_type": emergency["type"],
                            "metric": emergency["metric"],
                            "value": emergency["value"],
                            "description": emergency["description"],
                            "urgency": emergency["urgency"].value,
                            "trigger_type": "emergency_condition",
                            "requires_immediate_action": True
                        },
                        db=db
                    )
                    
                    emergency_alerts.append({
                        "emergency": emergency,
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to send emergency alert for user {user_id}: {e}")
            
            return emergency_alerts
            
        except Exception as e:
            logger.error(f"Failed to check emergency conditions for user {user_id}: {e}")
            return emergency_alerts
    
    async def send_contextual_notification(
        self,
        user_id: int,
        context: str,
        context_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Send a contextual notification based on specific context and data.
        
        Args:
            user_id: Target user ID
            context: Context type (health_metric, medication, appointment, etc.)
            context_data: Context-specific data
            db: Database session
            
        Returns:
            Dictionary with delivery results
        """
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise NotificationError(f"User not found: {user_id}")
            
            # Determine notification type and content based on context
            if context == "health_metric":
                return await self._send_health_metric_notification(user, context_data, db)
            elif context == "medication":
                return await self._send_medication_notification(user, context_data, db)
            elif context == "appointment":
                return await self._send_appointment_notification(user, context_data, db)
            elif context == "goal":
                return await self._send_goal_notification(user, context_data, db)
            elif context == "symptom":
                return await self._send_symptom_notification(user, context_data, db)
            else:
                raise NotificationError(f"Unknown context: {context}")
                
        except Exception as e:
            logger.error(f"Failed to send contextual notification for user {user_id}: {e}")
            raise NotificationError(f"Failed to send contextual notification: {e}")
    
    async def _send_health_metric_notification(
        self,
        user: User,
        context_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Send health metric notification."""
        metric_name = context_data.get("metric_name")
        metric_value = context_data.get("metric_value")
        trend = context_data.get("trend", "stable")
        
        title = f"Health Update: {metric_name.replace('_', ' ').title()}"
        message = f"Your {metric_name.replace('_', ' ')} is {metric_value}. "
        
        if trend == "improving":
            message += "Great news! This shows improvement. Keep up the good work!"
        elif trend == "declining":
            message += "This shows a decline. Please monitor closely and consult your healthcare provider if this continues."
        else:
            message += "This is within normal range. Continue monitoring as usual."
        
        return await self.send_smart_notification(
            user_id=user.id,
            notification_type=NotificationType.HEALTH_ALERT,
            title=title,
            message=message,
            context_data={
                **context_data,
                "trigger_type": "health_metric_update"
            },
            db=db
        )
    
    async def _send_medication_notification(
        self,
        user: User,
        context_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Send medication notification."""
        medication_name = context_data.get("medication_name")
        action = context_data.get("action", "reminder")
        
        if action == "reminder":
            title = f"Medication Reminder: {medication_name}"
            message = f"It's time to take your {medication_name}. Please take as prescribed."
        elif action == "refill":
            title = f"Medication Refill: {medication_name}"
            message = f"Your {medication_name} prescription needs a refill. Please contact your pharmacy or healthcare provider."
        else:
            title = f"Medication Update: {medication_name}"
            message = f"Update regarding your {medication_name}: {context_data.get('message', 'Please check your medication schedule.')}"
        
        return await self.send_smart_notification(
            user_id=user.id,
            notification_type=NotificationType.MEDICATION_REMINDER,
            title=title,
            message=message,
            context_data={
                **context_data,
                "trigger_type": "medication_update"
            },
            db=db
        )
    
    async def _send_appointment_notification(
        self,
        user: User,
        context_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Send appointment notification."""
        appointment_type = context_data.get("appointment_type", "appointment")
        appointment_time = context_data.get("appointment_time")
        time_until = context_data.get("time_until", "soon")
        
        title = f"Appointment Reminder: {appointment_type.title()}"
        message = f"Your {appointment_type} is {time_until}. "
        
        if appointment_time:
            message += f"Scheduled for {appointment_time.strftime('%B %d, %Y at %I:%M %p')}. "
        
        message += "Please prepare any questions or concerns you'd like to discuss."
        
        return await self.send_smart_notification(
            user_id=user.id,
            notification_type=NotificationType.APPOINTMENT_REMINDER,
            title=title,
            message=message,
            context_data={
                **context_data,
                "trigger_type": "appointment_reminder"
            },
            db=db
        )
    
    async def _send_goal_notification(
        self,
        user: User,
        context_data: Dict[str, Any],
        db: Session
        ) -> Dict[str, Any]:
        """Send goal achievement notification."""
        goal_name = context_data.get("goal_name", "health goal")
        achievement_type = context_data.get("achievement_type", "milestone")
        
        title = f"Goal Achievement: {goal_name}"
        
        if achievement_type == "completed":
            message = f"🎉 Congratulations! You've completed your goal: {goal_name}. Well done!"
        elif achievement_type == "milestone":
            message = f"🎯 Great progress! You've reached a milestone in your goal: {goal_name}. Keep going!"
        else:
            message = f"📈 Progress update on your goal: {goal_name}. You're making great strides!"
        
        return await self.send_smart_notification(
            user_id=user.id,
            notification_type=NotificationType.GOAL_ACHIEVEMENT,
            title=title,
            message=message,
            context_data={
                **context_data,
                "trigger_type": "goal_update"
            },
            db=db
        )
    
    async def _send_symptom_notification(
        self,
        user: User,
        context_data: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """Send symptom notification."""
        symptom_name = context_data.get("symptom_name", "symptom")
        severity = context_data.get("severity", "mild")
        trend = context_data.get("trend", "stable")
        
        title = f"Symptom Update: {symptom_name}"
        
        if trend == "worsening":
            message = f"Your {symptom_name} appears to be worsening. "
            if severity in ["moderate", "severe"]:
                message += "Please consider contacting your healthcare provider."
            else:
                message += "Please monitor closely and contact your healthcare provider if it continues to worsen."
        elif trend == "improving":
            message = f"Good news! Your {symptom_name} appears to be improving. Continue with your current treatment plan."
        else:
            message = f"Your {symptom_name} remains stable. Continue monitoring as recommended by your healthcare provider."
        
        return await self.send_smart_notification(
            user_id=user.id,
            notification_type=NotificationType.HEALTH_ALERT,
            title=title,
            message=message,
            context_data={
                **context_data,
                "trigger_type": "symptom_update"
            },
            db=db
        ) 