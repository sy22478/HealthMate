"""
Smart Notification Logic Service for HealthMate

This module provides:
- Intelligent notification prioritization and classification
- User preference-based filtering and time-zone aware scheduling
- Contextual notification triggers based on health metrics
- Emergency health alert system
- Notification frequency controls and quiet hours management
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import pytz
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

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
from app.utils.audit_logging import AuditLogger

logger = logging.getLogger(__name__)


class NotificationUrgency(str, Enum):
    """Notification urgency levels for classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class NotificationContext(str, Enum):
    """Notification context types."""
    HEALTH_METRIC = "health_metric"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    SYMPTOM = "symptom"
    GOAL = "goal"
    SYSTEM = "system"
    EMERGENCY = "emergency"


@dataclass
class NotificationTrigger:
    """Notification trigger configuration."""
    trigger_type: str
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    comparison_operator: str = ">"  # >, <, >=, <=, ==, !=
    time_window: Optional[timedelta] = None
    frequency_limit: Optional[int] = None  # Max notifications per time window
    enabled: bool = True


@dataclass
class HealthThreshold:
    """Health metric threshold configuration."""
    metric_name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    critical_min: Optional[float] = None
    critical_max: Optional[float] = None
    unit: str = ""
    description: str = ""


class SmartNotificationLogic:
    """Smart notification logic service for intelligent targeting and prioritization."""
    
    def __init__(self, settings: Settings):
        """Initialize the smart notification logic service."""
        self.settings = settings
        self.audit_logger = AuditLogger()
        
        # Health metric thresholds
        self.health_thresholds = self._initialize_health_thresholds()
        
        # Notification triggers
        self.notification_triggers = self._initialize_notification_triggers()
        
        logger.info("Smart notification logic service initialized")
    
    def _initialize_health_thresholds(self) -> Dict[str, HealthThreshold]:
        """Initialize health metric thresholds."""
        return {
            "blood_pressure_systolic": HealthThreshold(
                metric_name="blood_pressure_systolic",
                min_value=90,
                max_value=140,
                critical_min=70,
                critical_max=180,
                unit="mmHg",
                description="Systolic blood pressure"
            ),
            "blood_pressure_diastolic": HealthThreshold(
                metric_name="blood_pressure_diastolic",
                min_value=60,
                max_value=90,
                critical_min=40,
                critical_max=110,
                unit="mmHg",
                description="Diastolic blood pressure"
            ),
            "heart_rate": HealthThreshold(
                metric_name="heart_rate",
                min_value=60,
                max_value=100,
                critical_min=40,
                critical_max=150,
                unit="bpm",
                description="Heart rate"
            ),
            "blood_glucose": HealthThreshold(
                metric_name="blood_glucose",
                min_value=70,
                max_value=140,
                critical_min=50,
                critical_max=300,
                unit="mg/dL",
                description="Blood glucose level"
            ),
            "temperature": HealthThreshold(
                metric_name="temperature",
                min_value=97.0,
                max_value=99.5,
                critical_min=95.0,
                critical_max=103.0,
                unit="°F",
                description="Body temperature"
            ),
            "oxygen_saturation": HealthThreshold(
                metric_name="oxygen_saturation",
                min_value=95,
                max_value=100,
                critical_min=90,
                critical_max=100,
                unit="%",
                description="Blood oxygen saturation"
            ),
            "weight": HealthThreshold(
                metric_name="weight",
                min_value=30,
                max_value=300,
                critical_min=20,
                critical_max=400,
                unit="kg",
                description="Body weight"
            )
        }
    
    def _initialize_notification_triggers(self) -> Dict[str, NotificationTrigger]:
        """Initialize notification triggers."""
        return {
            "high_blood_pressure": NotificationTrigger(
                trigger_type="health_metric",
                metric_name="blood_pressure_systolic",
                threshold_value=140,
                comparison_operator=">",
                time_window=timedelta(hours=1),
                frequency_limit=3
            ),
            "low_blood_pressure": NotificationTrigger(
                trigger_type="health_metric",
                metric_name="blood_pressure_systolic",
                threshold_value=90,
                comparison_operator="<",
                time_window=timedelta(hours=1),
                frequency_limit=3
            ),
            "high_heart_rate": NotificationTrigger(
                trigger_type="health_metric",
                metric_name="heart_rate",
                threshold_value=100,
                comparison_operator=">",
                time_window=timedelta(minutes=30),
                frequency_limit=5
            ),
            "low_heart_rate": NotificationTrigger(
                trigger_type="health_metric",
                metric_name="heart_rate",
                threshold_value=60,
                comparison_operator="<",
                time_window=timedelta(minutes=30),
                frequency_limit=5
            ),
            "high_blood_glucose": NotificationTrigger(
                trigger_type="health_metric",
                metric_name="blood_glucose",
                threshold_value=140,
                comparison_operator=">",
                time_window=timedelta(hours=2),
                frequency_limit=2
            ),
            "low_blood_glucose": NotificationTrigger(
                trigger_type="health_metric",
                metric_name="blood_glucose",
                threshold_value=70,
                comparison_operator="<",
                time_window=timedelta(hours=2),
                frequency_limit=2
            ),
            "medication_missed": NotificationTrigger(
                trigger_type="medication",
                time_window=timedelta(hours=1),
                frequency_limit=3
            ),
            "appointment_reminder": NotificationTrigger(
                trigger_type="appointment",
                time_window=timedelta(hours=24),
                frequency_limit=2
            )
        }
    
    def classify_notification_urgency(
        self,
        notification_type: NotificationType,
        context_data: Optional[Dict[str, Any]] = None,
        user: Optional[User] = None
    ) -> NotificationUrgency:
        """
        Classify notification urgency based on type and context.
        
        Args:
            notification_type: Type of notification
            context_data: Additional context data
            user: Target user (for personalized classification)
            
        Returns:
            Notification urgency level
        """
        # Emergency alerts are always critical
        if notification_type == NotificationType.EMERGENCY_ALERT:
            return NotificationUrgency.EMERGENCY
        
        # Health alerts based on severity
        if notification_type == NotificationType.HEALTH_ALERT:
            if context_data and "severity" in context_data:
                severity = context_data["severity"]
                if severity == "critical":
                    return NotificationUrgency.CRITICAL
                elif severity == "high":
                    return NotificationUrgency.HIGH
                elif severity == "medium":
                    return NotificationUrgency.MEDIUM
                else:
                    return NotificationUrgency.LOW
        
        # Medication reminders - high urgency for missed doses
        if notification_type == NotificationType.MEDICATION_REMINDER:
            if context_data and context_data.get("is_missed_dose", False):
                return NotificationUrgency.HIGH
            else:
                return NotificationUrgency.MEDIUM
        
        # Appointment reminders - medium urgency
        if notification_type == NotificationType.APPOINTMENT_REMINDER:
            if context_data and context_data.get("is_urgent_appointment", False):
                return NotificationUrgency.HIGH
            else:
                return NotificationUrgency.MEDIUM
        
        # Goal achievements - low urgency
        if notification_type == NotificationType.GOAL_ACHIEVEMENT:
            return NotificationUrgency.LOW
        
        # Weekly/monthly reports - low urgency
        if notification_type in [NotificationType.WEEKLY_SUMMARY, NotificationType.MONTHLY_REPORT]:
            return NotificationUrgency.LOW
        
        # Default to medium urgency
        return NotificationUrgency.MEDIUM
    
    def should_send_notification(
        self,
        user: User,
        notification_type: NotificationType,
        urgency: NotificationUrgency,
        context_data: Optional[Dict[str, Any]] = None,
        db: Session = None
    ) -> Tuple[bool, str]:
        """
        Determine if a notification should be sent based on user preferences and frequency controls.
        
        Args:
            user: Target user
            notification_type: Type of notification
            urgency: Notification urgency
            context_data: Additional context data
            db: Database session
            
        Returns:
            Tuple of (should_send, reason)
        """
        try:
            # Get user preferences
            prefs = user.notification_preferences
            if not prefs:
                return True, "No preferences set, defaulting to allow"
            
            # Check if user has disabled this notification type
            type_prefs = prefs.preferences.get(notification_type.value, {})
            if not type_prefs.get("enabled", True):
                return False, f"Notification type {notification_type.value} disabled by user"
            
            # Check minimum priority filter
            min_priority = type_prefs.get("min_priority", "low")
            if not self._is_urgency_higher_or_equal(urgency.value, min_priority):
                return False, f"Urgency {urgency.value} below minimum {min_priority}"
            
            # Check quiet hours
            if self._is_in_quiet_hours(user, prefs):
                # Allow emergency notifications during quiet hours
                if urgency in [NotificationUrgency.CRITICAL, NotificationUrgency.EMERGENCY]:
                    return True, "Emergency notification allowed during quiet hours"
                else:
                    return False, "Notification blocked by quiet hours"
            
            # Check daily notification limit
            if not self._check_daily_limit(user, prefs, db):
                return False, "Daily notification limit exceeded"
            
            # Check frequency limits for specific triggers
            if context_data and "trigger_type" in context_data:
                trigger_type = context_data["trigger_type"]
                if not self._check_frequency_limit(user, trigger_type, db):
                    return False, f"Frequency limit exceeded for trigger {trigger_type}"
            
            return True, "Notification allowed"
            
        except Exception as e:
            logger.error(f"Error checking notification send criteria: {e}")
            return True, f"Error in check, defaulting to allow: {e}"
    
    def _is_urgency_higher_or_equal(self, urgency: str, min_urgency: str) -> bool:
        """Check if urgency is higher or equal to minimum urgency."""
        urgency_order = {
            NotificationUrgency.LOW.value: 1,
            NotificationUrgency.MEDIUM.value: 2,
            NotificationUrgency.HIGH.value: 3,
            NotificationUrgency.CRITICAL.value: 4,
            NotificationUrgency.EMERGENCY.value: 5
        }
        
        return urgency_order.get(urgency, 0) >= urgency_order.get(min_urgency, 0)
    
    def _is_in_quiet_hours(self, user: User, prefs: UserNotificationPreference) -> bool:
        """Check if current time is within user's quiet hours."""
        if not prefs.quiet_hours_start or not prefs.quiet_hours_end:
            return False
        
        try:
            # Get user's timezone
            user_tz = pytz.timezone(prefs.timezone or "UTC")
            current_time = datetime.now(user_tz).time()
            
            # Parse quiet hours
            start_time = datetime.strptime(prefs.quiet_hours_start, "%H:%M").time()
            end_time = datetime.strptime(prefs.quiet_hours_end, "%H:%M").time()
            
            # Handle overnight quiet hours
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.error(f"Error checking quiet hours: {e}")
            return False
    
    def _check_daily_limit(self, user: User, prefs: UserNotificationPreference, db: Session) -> bool:
        """Check if user has exceeded daily notification limit."""
        try:
            # Count notifications sent today
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today_start + timedelta(days=1)
            
            notification_count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user.id,
                    Notification.created_at >= today_start,
                    Notification.created_at < today_end,
                    Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED])
                )
            ).count()
            
            return notification_count < prefs.max_daily_notifications
            
        except Exception as e:
            logger.error(f"Error checking daily limit: {e}")
            return True  # Default to allow if error
    
    def _check_frequency_limit(self, user: User, trigger_type: str, db: Session) -> bool:
        """Check frequency limit for specific trigger types."""
        try:
            trigger = self.notification_triggers.get(trigger_type)
            if not trigger or not trigger.frequency_limit:
                return True
            
            # Count recent notifications for this trigger
            time_window_start = datetime.now() - trigger.time_window
            
            notification_count = db.query(Notification).filter(
                and_(
                    Notification.user_id == user.id,
                    Notification.created_at >= time_window_start,
                    Notification.metadata.contains({"trigger_type": trigger_type}),
                    Notification.status.in_([NotificationStatus.SENT, NotificationStatus.DELIVERED])
                )
            ).count()
            
            return notification_count < trigger.frequency_limit
            
        except Exception as e:
            logger.error(f"Error checking frequency limit: {e}")
            return True  # Default to allow if error
    
    def get_optimal_send_time(
        self,
        user: User,
        notification_type: NotificationType,
        urgency: NotificationUrgency
    ) -> datetime:
        """
        Calculate optimal send time based on user preferences and notification type.
        
        Args:
            user: Target user
            notification_type: Type of notification
            urgency: Notification urgency
            
        Returns:
            Optimal send time
        """
        try:
            prefs = user.notification_preferences
            if not prefs:
                return datetime.now()
            
            # Emergency notifications should be sent immediately
            if urgency in [NotificationUrgency.CRITICAL, NotificationUrgency.EMERGENCY]:
                return datetime.now()
            
            # Get user's timezone
            user_tz = pytz.timezone(prefs.timezone or "UTC")
            current_time = datetime.now(user_tz)
            
            # Check if we're in quiet hours
            if self._is_in_quiet_hours(user, prefs):
                # Schedule for after quiet hours
                if prefs.quiet_hours_end:
                    end_time = datetime.strptime(prefs.quiet_hours_end, "%H:%M").time()
                    next_send = current_time.replace(
                        hour=end_time.hour,
                        minute=end_time.minute,
                        second=0,
                        microsecond=0
                    )
                    
                    # If the time has passed today, schedule for tomorrow
                    if next_send <= current_time:
                        next_send += timedelta(days=1)
                    
                    return next_send.replace(tzinfo=user_tz)
            
            # For non-urgent notifications, consider user's preferred times
            type_prefs = prefs.preferences.get(notification_type.value, {})
            preferred_time = type_prefs.get("preferred_time")
            
            if preferred_time:
                try:
                    preferred_hour, preferred_minute = map(int, preferred_time.split(":"))
                    next_send = current_time.replace(
                        hour=preferred_hour,
                        minute=preferred_minute,
                        second=0,
                        microsecond=0
                    )
                    
                    # If the time has passed today, schedule for tomorrow
                    if next_send <= current_time:
                        next_send += timedelta(days=1)
                    
                    return next_send.replace(tzinfo=user_tz)
                except Exception as e:
                    logger.error(f"Error parsing preferred time: {e}")
            
            # Default to immediate send
            return datetime.now()
            
        except Exception as e:
            logger.error(f"Error calculating optimal send time: {e}")
            return datetime.now()
    
    def check_health_metric_thresholds(
        self,
        user: User,
        metric_name: str,
        metric_value: float,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Check if health metric values exceed thresholds and generate alerts.
        
        Args:
            user: Target user
            metric_name: Name of the health metric
            metric_value: Current metric value
            db: Database session
            
        Returns:
            List of threshold violations and alert configurations
        """
        alerts = []
        
        try:
            threshold = self.health_thresholds.get(metric_name)
            if not threshold:
                return alerts
            
            # Check critical thresholds first
            if threshold.critical_min is not None and metric_value < threshold.critical_min:
                alerts.append({
                    "type": "critical_low",
                    "metric": metric_name,
                    "value": metric_value,
                    "threshold": threshold.critical_min,
                    "unit": threshold.unit,
                    "description": f"Critical low {threshold.description}",
                    "urgency": NotificationUrgency.CRITICAL,
                    "notification_type": NotificationType.HEALTH_ALERT
                })
            
            if threshold.critical_max is not None and metric_value > threshold.critical_max:
                alerts.append({
                    "type": "critical_high",
                    "metric": metric_name,
                    "value": metric_value,
                    "threshold": threshold.critical_max,
                    "unit": threshold.unit,
                    "description": f"Critical high {threshold.description}",
                    "urgency": NotificationUrgency.CRITICAL,
                    "notification_type": NotificationType.HEALTH_ALERT
                })
            
            # Check normal thresholds
            if threshold.min_value is not None and metric_value < threshold.min_value:
                alerts.append({
                    "type": "low",
                    "metric": metric_name,
                    "value": metric_value,
                    "threshold": threshold.min_value,
                    "unit": threshold.unit,
                    "description": f"Low {threshold.description}",
                    "urgency": NotificationUrgency.HIGH,
                    "notification_type": NotificationType.HEALTH_ALERT
                })
            
            if threshold.max_value is not None and metric_value > threshold.max_value:
                alerts.append({
                    "type": "high",
                    "metric": metric_name,
                    "value": metric_value,
                    "threshold": threshold.max_value,
                    "unit": threshold.unit,
                    "description": f"High {threshold.description}",
                    "urgency": NotificationUrgency.HIGH,
                    "notification_type": NotificationType.HEALTH_ALERT
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking health metric thresholds: {e}")
            return alerts
    
    def check_medication_reminders(
        self,
        user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Check for missed medication doses and generate reminders.
        
        Args:
            user: Target user
            db: Database session
            
        Returns:
            List of medication reminders
        """
        reminders = []
        
        try:
            # Get user's active medications
            active_medications = db.query(EnhancedMedication).filter(
                and_(
                    EnhancedMedication.user_id == user.id,
                    EnhancedMedication.status == "active"
                )
            ).all()
            
            current_time = datetime.now()
            
            for medication in active_medications:
                # Check if medication is due
                if medication.next_dose_time and medication.next_dose_time <= current_time:
                    # Check if dose was taken
                    recent_dose = db.query(MedicationDoseLog).filter(
                        and_(
                            MedicationDoseLog.medication_id == medication.id,
                            MedicationDoseLog.taken_at >= medication.next_dose_time - timedelta(hours=2),
                            MedicationDoseLog.taken_at <= medication.next_dose_time + timedelta(hours=2)
                        )
                    ).first()
                    
                    if not recent_dose:
                        # Generate missed dose reminder
                        reminders.append({
                            "type": "missed_dose",
                            "medication_id": medication.id,
                            "medication_name": medication.medication_name,
                            "scheduled_time": medication.next_dose_time,
                            "description": f"Missed dose of {medication.medication_name}",
                            "urgency": NotificationUrgency.HIGH,
                            "notification_type": NotificationType.MEDICATION_REMINDER
                        })
                
                # Check for upcoming doses
                elif medication.next_dose_time and medication.next_dose_time <= current_time + timedelta(hours=1):
                    reminders.append({
                        "type": "upcoming_dose",
                        "medication_id": medication.id,
                        "medication_name": medication.medication_name,
                        "scheduled_time": medication.next_dose_time,
                        "description": f"Upcoming dose of {medication.medication_name}",
                        "urgency": NotificationUrgency.MEDIUM,
                        "notification_type": NotificationType.MEDICATION_REMINDER
                    })
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error checking medication reminders: {e}")
            return reminders
    
    def check_emergency_conditions(
        self,
        user: User,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Check for emergency health conditions that require immediate attention.
        
        Args:
            user: Target user
            db: Database session
            
        Returns:
            List of emergency alerts
        """
        emergencies = []
        
        try:
            # Get recent health data
            recent_data = db.query(HealthData).filter(
                and_(
                    HealthData.user_id == user.id,
                    HealthData.timestamp >= datetime.now() - timedelta(hours=24)
                )
            ).all()
            
            for data_point in recent_data:
                # Check for critical health values
                if data_point.data_type == "heart_rate":
                    try:
                        heart_rate = float(data_point.value)
                        if heart_rate > 150 or heart_rate < 40:
                            emergencies.append({
                                "type": "critical_heart_rate",
                                "metric": "heart_rate",
                                "value": heart_rate,
                                "description": f"Critical heart rate: {heart_rate} bpm",
                                "urgency": NotificationUrgency.EMERGENCY,
                                "notification_type": NotificationType.EMERGENCY_ALERT
                            })
                    except (ValueError, TypeError):
                        continue
                
                elif data_point.data_type == "blood_pressure":
                    try:
                        bp_data = data_point.value
                        if isinstance(bp_data, dict):
                            systolic = float(bp_data.get("systolic", 0))
                            diastolic = float(bp_data.get("diastolic", 0))
                            
                            if systolic > 180 or systolic < 70 or diastolic > 110 or diastolic < 40:
                                emergencies.append({
                                    "type": "critical_blood_pressure",
                                    "metric": "blood_pressure",
                                    "value": {"systolic": systolic, "diastolic": diastolic},
                                    "description": f"Critical blood pressure: {systolic}/{diastolic} mmHg",
                                    "urgency": NotificationUrgency.EMERGENCY,
                                    "notification_type": NotificationType.EMERGENCY_ALERT
                                })
                    except (ValueError, TypeError):
                        continue
                
                elif data_point.data_type == "blood_glucose":
                    try:
                        glucose = float(data_point.value)
                        if glucose > 300 or glucose < 50:
                            emergencies.append({
                                "type": "critical_blood_glucose",
                                "metric": "blood_glucose",
                                "value": glucose,
                                "description": f"Critical blood glucose: {glucose} mg/dL",
                                "urgency": NotificationUrgency.EMERGENCY,
                                "notification_type": NotificationType.EMERGENCY_ALERT
                            })
                    except (ValueError, TypeError):
                        continue
            
            return emergencies
            
        except Exception as e:
            logger.error(f"Error checking emergency conditions: {e}")
            return emergencies
    
    def get_notification_channels_by_urgency(
        self,
        user: User,
        urgency: NotificationUrgency,
        notification_type: NotificationType
    ) -> List[NotificationChannel]:
        """
        Determine optimal notification channels based on urgency and user preferences.
        
        Args:
            user: Target user
            urgency: Notification urgency
            notification_type: Type of notification
            
        Returns:
            List of channels in order of preference
        """
        channels = []
        prefs = user.notification_preferences
        
        if not prefs:
            return [NotificationChannel.EMAIL]
        
        # Emergency notifications: All available channels
        if urgency == NotificationUrgency.EMERGENCY:
            if prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            return channels
        
        # Critical notifications: SMS + Push + Email
        elif urgency == NotificationUrgency.CRITICAL:
            if prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            return channels
        
        # High urgency: Push + SMS + Email
        elif urgency == NotificationUrgency.HIGH:
            if prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            if prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            return channels
        
        # Medium urgency: Push + Email
        elif urgency == NotificationUrgency.MEDIUM:
            if prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            if prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if prefs.sms_enabled:
                channels.append(NotificationChannel.SMS)
            return channels
        
        # Low urgency: Email + Push
        elif urgency == NotificationUrgency.LOW:
            if prefs.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if prefs.push_enabled:
                channels.append(NotificationChannel.PUSH)
            return channels
        
        # Default fallback
        if prefs.email_enabled:
            channels.append(NotificationChannel.EMAIL)
        elif prefs.push_enabled:
            channels.append(NotificationChannel.PUSH)
        elif prefs.sms_enabled:
            channels.append(NotificationChannel.SMS)
        
        return channels 