"""
Tests for Smart Notification Logic

This module tests:
- Smart notification logic service
- Enhanced notification service
- Notification urgency classification
- Health metric threshold checking
- Medication reminder processing
- Emergency condition monitoring
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.smart_notification_logic import (
    SmartNotificationLogic, NotificationUrgency, NotificationContext,
    NotificationTrigger, HealthThreshold
)
from app.services.enhanced_notification_service import EnhancedNotificationService
from app.models.notification_models import (
    NotificationType, NotificationPriority, NotificationChannel, NotificationStatus,
    UserNotificationPreference
)
from app.models.user import User
from app.models.health_data import HealthData
from app.models.enhanced_health_models import EnhancedMedication, MedicationDoseLog
from app.config import Settings


class TestSmartNotificationLogic:
    """Test smart notification logic functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    def smart_logic(self, settings):
        """Create smart notification logic instance."""
        return SmartNotificationLogic(settings)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.phone = "+1234567890"
        return user
    
    @pytest.fixture
    def mock_preferences(self):
        """Create mock notification preferences."""
        prefs = Mock(spec=UserNotificationPreference)
        prefs.email_enabled = True
        prefs.sms_enabled = True
        prefs.push_enabled = True
        prefs.max_daily_notifications = 10
        prefs.quiet_hours_start = "22:00"
        prefs.quiet_hours_end = "08:00"
        prefs.timezone = "UTC"
        prefs.preferences = {
            "health_alert": {
                "enabled": True,
                "min_priority": "medium",
                "preferred_channel": "email"
            },
            "medication_reminder": {
                "enabled": True,
                "min_priority": "high",
                "preferred_channel": "sms"
            }
        }
        return prefs
    
    def test_initialize_health_thresholds(self, smart_logic):
        """Test health threshold initialization."""
        thresholds = smart_logic.health_thresholds
        
        assert "blood_pressure_systolic" in thresholds
        assert "heart_rate" in thresholds
        assert "blood_glucose" in thresholds
        assert "temperature" in thresholds
        
        # Check specific threshold values
        bp_threshold = thresholds["blood_pressure_systolic"]
        assert bp_threshold.min_value == 90
        assert bp_threshold.max_value == 140
        assert bp_threshold.critical_min == 70
        assert bp_threshold.critical_max == 180
        assert bp_threshold.unit == "mmHg"
    
    def test_initialize_notification_triggers(self, smart_logic):
        """Test notification trigger initialization."""
        triggers = smart_logic.notification_triggers
        
        assert "high_blood_pressure" in triggers
        assert "low_blood_pressure" in triggers
        assert "high_heart_rate" in triggers
        assert "medication_missed" in triggers
        
        # Check specific trigger configuration
        bp_trigger = triggers["high_blood_pressure"]
        assert bp_trigger.metric_name == "blood_pressure_systolic"
        assert bp_trigger.threshold_value == 140
        assert bp_trigger.comparison_operator == ">"
        assert bp_trigger.frequency_limit == 3
    
    def test_classify_notification_urgency_emergency(self, smart_logic):
        """Test emergency notification urgency classification."""
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.EMERGENCY_ALERT
        )
        assert urgency == NotificationUrgency.EMERGENCY
    
    def test_classify_notification_urgency_health_alert(self, smart_logic):
        """Test health alert urgency classification."""
        # Test with critical severity
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.HEALTH_ALERT,
            context_data={"severity": "critical"}
        )
        assert urgency == NotificationUrgency.CRITICAL
        
        # Test with high severity
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.HEALTH_ALERT,
            context_data={"severity": "high"}
        )
        assert urgency == NotificationUrgency.HIGH
        
        # Test with medium severity
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.HEALTH_ALERT,
            context_data={"severity": "medium"}
        )
        assert urgency == NotificationUrgency.MEDIUM
    
    def test_classify_notification_urgency_medication_reminder(self, smart_logic):
        """Test medication reminder urgency classification."""
        # Test missed dose
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.MEDICATION_REMINDER,
            context_data={"is_missed_dose": True}
        )
        assert urgency == NotificationUrgency.HIGH
        
        # Test regular reminder
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.MEDICATION_REMINDER,
            context_data={"is_missed_dose": False}
        )
        assert urgency == NotificationUrgency.MEDIUM
    
    def test_classify_notification_urgency_goal_achievement(self, smart_logic):
        """Test goal achievement urgency classification."""
        urgency = smart_logic.classify_notification_urgency(
            NotificationType.GOAL_ACHIEVEMENT
        )
        assert urgency == NotificationUrgency.LOW
    
    def test_should_send_notification_enabled(self, smart_logic, mock_user, mock_preferences):
        """Test notification should be sent when enabled."""
        mock_user.notification_preferences = mock_preferences
        
        should_send, reason = smart_logic.should_send_notification(
            mock_user,
            NotificationType.HEALTH_ALERT,
            NotificationUrgency.HIGH,
            db=Mock()
        )
        
        assert should_send is True
        assert "allowed" in reason.lower()
    
    def test_should_send_notification_disabled(self, smart_logic, mock_user, mock_preferences):
        """Test notification should not be sent when disabled."""
        mock_preferences.preferences["health_alert"]["enabled"] = False
        mock_user.notification_preferences = mock_preferences
        
        should_send, reason = smart_logic.should_send_notification(
            mock_user,
            NotificationType.HEALTH_ALERT,
            NotificationUrgency.HIGH,
            db=Mock()
        )
        
        assert should_send is False
        assert "disabled" in reason.lower()
    
    def test_should_send_notification_priority_filter(self, smart_logic, mock_user, mock_preferences):
        """Test notification priority filtering."""
        mock_preferences.preferences["health_alert"]["min_priority"] = "high"
        mock_user.notification_preferences = mock_preferences
        
        # Test with low priority (should be filtered out)
        should_send, reason = smart_logic.should_send_notification(
            mock_user,
            NotificationType.HEALTH_ALERT,
            NotificationUrgency.LOW,
            db=Mock()
        )
        
        assert should_send is False
        assert "below minimum" in reason.lower()
        
        # Test with high priority (should be allowed)
        should_send, reason = smart_logic.should_send_notification(
            mock_user,
            NotificationType.HEALTH_ALERT,
            NotificationUrgency.HIGH,
            db=Mock()
        )
        
        assert should_send is True
    
    def test_is_urgency_higher_or_equal(self, smart_logic):
        """Test urgency comparison."""
        # Test higher urgency
        assert smart_logic._is_urgency_higher_or_equal("high", "medium") is True
        assert smart_logic._is_urgency_higher_or_equal("critical", "high") is True
        assert smart_logic._is_urgency_higher_or_equal("emergency", "critical") is True
        
        # Test equal urgency
        assert smart_logic._is_urgency_higher_or_equal("high", "high") is True
        
        # Test lower urgency
        assert smart_logic._is_urgency_higher_or_equal("low", "high") is False
        assert smart_logic._is_urgency_higher_or_equal("medium", "critical") is False
    
    def test_is_in_quiet_hours(self, smart_logic, mock_preferences):
        """Test quiet hours detection."""
        # Test during quiet hours (22:00 - 08:00)
        with patch('app.services.smart_notification_logic.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 23, 0)  # 11 PM
            assert smart_logic._is_in_quiet_hours(mock_preferences) is True
            
            mock_datetime.now.return_value = datetime(2024, 1, 1, 2, 0)  # 2 AM
            assert smart_logic._is_in_quiet_hours(mock_preferences) is True
        
        # Test outside quiet hours
        with patch('app.services.smart_notification_logic.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 1, 12, 0)  # 12 PM
            assert smart_logic._is_in_quiet_hours(mock_preferences) is False
    
    def test_check_health_metric_thresholds_normal(self, smart_logic, mock_user):
        """Test health metric threshold checking with normal values."""
        alerts = smart_logic.check_health_metric_thresholds(
            mock_user, "heart_rate", 75.0, Mock()
        )
        assert len(alerts) == 0  # No alerts for normal heart rate
    
    def test_check_health_metric_thresholds_high(self, smart_logic, mock_user):
        """Test health metric threshold checking with high values."""
        alerts = smart_logic.check_health_metric_thresholds(
            mock_user, "heart_rate", 120.0, Mock()
        )
        assert len(alerts) == 1
        assert alerts[0]["type"] == "high"
        assert alerts[0]["metric"] == "heart_rate"
        assert alerts[0]["value"] == 120.0
        assert alerts[0]["urgency"] == NotificationUrgency.HIGH
    
    def test_check_health_metric_thresholds_critical(self, smart_logic, mock_user):
        """Test health metric threshold checking with critical values."""
        alerts = smart_logic.check_health_metric_thresholds(
            mock_user, "heart_rate", 160.0, Mock()
        )
        assert len(alerts) == 1
        assert alerts[0]["type"] == "critical_high"
        assert alerts[0]["urgency"] == NotificationUrgency.CRITICAL
    
    def test_check_health_metric_thresholds_low(self, smart_logic, mock_user):
        """Test health metric threshold checking with low values."""
        alerts = smart_logic.check_health_metric_thresholds(
            mock_user, "heart_rate", 45.0, Mock()
        )
        assert len(alerts) == 1
        assert alerts[0]["type"] == "critical_low"
        assert alerts[0]["urgency"] == NotificationUrgency.CRITICAL
    
    def test_check_medication_reminders(self, smart_logic, mock_user):
        """Test medication reminder checking."""
        # Mock database session
        mock_db = Mock()
        
        # Mock active medication
        mock_medication = Mock(spec=EnhancedMedication)
        mock_medication.id = 1
        mock_medication.medication_name = "Test Medication"
        mock_medication.next_dose_time = datetime.now() - timedelta(hours=1)  # Missed dose
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_medication]
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No recent dose
        
        reminders = smart_logic.check_medication_reminders(mock_user, mock_db)
        
        assert len(reminders) == 1
        assert reminders[0]["type"] == "missed_dose"
        assert reminders[0]["medication_name"] == "Test Medication"
        assert reminders[0]["urgency"] == NotificationUrgency.HIGH
    
    def test_check_emergency_conditions(self, smart_logic, mock_user):
        """Test emergency condition checking."""
        # Mock database session
        mock_db = Mock()
        
        # Mock health data with critical values
        mock_health_data = Mock(spec=HealthData)
        mock_health_data.data_type = "heart_rate"
        mock_health_data.value = 180.0  # Critical high heart rate
        mock_health_data.timestamp = datetime.now()
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_health_data]
        
        emergencies = smart_logic.check_emergency_conditions(mock_user, mock_db)
        
        assert len(emergencies) == 1
        assert emergencies[0]["type"] == "critical_heart_rate"
        assert emergencies[0]["urgency"] == NotificationUrgency.EMERGENCY
    
    def test_get_notification_channels_by_urgency_emergency(self, smart_logic, mock_user, mock_preferences):
        """Test channel selection for emergency notifications."""
        mock_user.notification_preferences = mock_preferences
        
        channels = smart_logic.get_notification_channels_by_urgency(
            mock_user, NotificationUrgency.EMERGENCY, NotificationType.EMERGENCY_ALERT
        )
        
        # Emergency should use all channels, SMS first
        assert channels[0] == NotificationChannel.SMS
        assert NotificationChannel.PUSH in channels
        assert NotificationChannel.EMAIL in channels
    
    def test_get_notification_channels_by_urgency_low(self, smart_logic, mock_user, mock_preferences):
        """Test channel selection for low urgency notifications."""
        mock_user.notification_preferences = mock_preferences
        
        channels = smart_logic.get_notification_channels_by_urgency(
            mock_user, NotificationUrgency.LOW, NotificationType.WEEKLY_SUMMARY
        )
        
        # Low urgency should use email first, then push
        assert channels[0] == NotificationChannel.EMAIL
        assert channels[1] == NotificationChannel.PUSH
        assert NotificationChannel.SMS not in channels


class TestEnhancedNotificationService:
    """Test enhanced notification service functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    def enhanced_service(self, settings):
        """Create enhanced notification service instance."""
        return EnhancedNotificationService(settings)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.phone = "+1234567890"
        return user
    
    @pytest.fixture
    def mock_preferences(self):
        """Create mock notification preferences."""
        prefs = Mock(spec=UserNotificationPreference)
        prefs.email_enabled = True
        prefs.sms_enabled = True
        prefs.push_enabled = True
        prefs.max_daily_notifications = 10
        prefs.preferences = {
            "health_alert": {"enabled": True, "min_priority": "medium"},
            "medication_reminder": {"enabled": True, "min_priority": "high"}
        }
        return prefs
    
    @pytest.mark.asyncio
    async def test_send_smart_notification_success(self, enhanced_service, mock_user, mock_preferences):
        """Test successful smart notification sending."""
        mock_user.notification_preferences = mock_preferences
        
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock notification service
        enhanced_service.notification_service.send_notification = Mock()
        enhanced_service.notification_service.send_notification.return_value = {
            "notification_id": 123,
            "success": True,
            "channels_attempted": ["email"]
        }
        
        result = await enhanced_service.send_smart_notification(
            user_id=1,
            notification_type=NotificationType.HEALTH_ALERT,
            title="Test Alert",
            message="Test message",
            db=mock_db
        )
        
        assert result["notification_id"] == 123
        assert result["success"] is True
        assert result["urgency"] == "medium"  # Default for health alert
    
    @pytest.mark.asyncio
    async def test_send_smart_notification_user_not_found(self, enhanced_service):
        """Test smart notification with non-existent user."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(Exception) as exc_info:
            await enhanced_service.send_smart_notification(
                user_id=999,
                notification_type=NotificationType.HEALTH_ALERT,
                title="Test Alert",
                message="Test message",
                db=mock_db
            )
        
        assert "User not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_send_smart_notification_disabled(self, enhanced_service, mock_user, mock_preferences):
        """Test smart notification when disabled by user preferences."""
        mock_preferences.preferences["health_alert"]["enabled"] = False
        mock_user.notification_preferences = mock_preferences
        
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = await enhanced_service.send_smart_notification(
            user_id=1,
            notification_type=NotificationType.HEALTH_ALERT,
            title="Test Alert",
            message="Test message",
            db=mock_db
        )
        
        assert result["sent"] is False
        assert "disabled" in result["reason"].lower()
    
    def test_urgency_to_priority(self, enhanced_service):
        """Test urgency to priority conversion."""
        assert enhanced_service._urgency_to_priority(NotificationUrgency.LOW) == NotificationPriority.LOW
        assert enhanced_service._urgency_to_priority(NotificationUrgency.MEDIUM) == NotificationPriority.NORMAL
        assert enhanced_service._urgency_to_priority(NotificationUrgency.HIGH) == NotificationPriority.HIGH
        assert enhanced_service._urgency_to_priority(NotificationUrgency.CRITICAL) == NotificationPriority.URGENT
        assert enhanced_service._urgency_to_priority(NotificationUrgency.EMERGENCY) == NotificationPriority.EMERGENCY
    
    @pytest.mark.asyncio
    async def test_monitor_health_metrics_and_alert(self, enhanced_service, mock_user):
        """Test health metrics monitoring and alerting."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock health data
        mock_health_data = Mock(spec=HealthData)
        mock_health_data.data_type = "heart_rate"
        mock_health_data.value = 120.0  # High heart rate
        mock_health_data.timestamp = datetime.now()
        
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_health_data]
        
        # Mock smart notification sending
        enhanced_service.send_smart_notification = Mock()
        enhanced_service.send_smart_notification.return_value = {
            "notification_id": 123,
            "success": True
        }
        
        alerts = await enhanced_service.monitor_health_metrics_and_alert(1, mock_db)
        
        assert len(alerts) == 1
        assert alerts[0]["alert"]["type"] == "high"
        assert alerts[0]["result"]["notification_id"] == 123
    
    @pytest.mark.asyncio
    async def test_process_medication_reminders(self, enhanced_service, mock_user):
        """Test medication reminder processing."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock smart logic
        enhanced_service.smart_logic.check_medication_reminders = Mock()
        enhanced_service.smart_logic.check_medication_reminders.return_value = [
            {
                "type": "missed_dose",
                "medication_id": 1,
                "medication_name": "Test Medication",
                "scheduled_time": datetime.now(),
                "urgency": NotificationUrgency.HIGH,
                "notification_type": NotificationType.MEDICATION_REMINDER
            }
        ]
        
        # Mock smart notification sending
        enhanced_service.send_smart_notification = Mock()
        enhanced_service.send_smart_notification.return_value = {
            "notification_id": 123,
            "success": True
        }
        
        reminders = await enhanced_service.process_medication_reminders(1, mock_db)
        
        assert len(reminders) == 1
        assert reminders[0]["alert"]["medication_name"] == "Test Medication"
        assert reminders[0]["result"]["notification_id"] == 123
    
    @pytest.mark.asyncio
    async def test_check_emergency_conditions(self, enhanced_service, mock_user):
        """Test emergency condition checking."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock smart logic
        enhanced_service.smart_logic.check_emergency_conditions = Mock()
        enhanced_service.smart_logic.check_emergency_conditions.return_value = [
            {
                "type": "critical_heart_rate",
                "metric": "heart_rate",
                "value": 180.0,
                "description": "Critical heart rate",
                "urgency": NotificationUrgency.EMERGENCY,
                "notification_type": NotificationType.EMERGENCY_ALERT
            }
        ]
        
        # Mock smart notification sending
        enhanced_service.send_smart_notification = Mock()
        enhanced_service.send_smart_notification.return_value = {
            "notification_id": 123,
            "success": True
        }
        
        emergencies = await enhanced_service.check_emergency_conditions(1, mock_db)
        
        assert len(emergencies) == 1
        assert emergencies[0]["emergency"]["type"] == "critical_heart_rate"
        assert emergencies[0]["result"]["notification_id"] == 123
    
    @pytest.mark.asyncio
    async def test_send_contextual_notification_health_metric(self, enhanced_service, mock_user):
        """Test contextual notification for health metric."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # Mock smart notification sending
        enhanced_service.send_smart_notification = Mock()
        enhanced_service.send_smart_notification.return_value = {
            "notification_id": 123,
            "success": True
        }
        
        context_data = {
            "metric_name": "heart_rate",
            "metric_value": 75.0,
            "trend": "stable"
        }
        
        result = await enhanced_service.send_contextual_notification(
            user_id=1,
            context="health_metric",
            context_data=context_data,
            db=mock_db
        )
        
        assert result["notification_id"] == 123
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_send_contextual_notification_unknown_context(self, enhanced_service, mock_user):
        """Test contextual notification with unknown context."""
        # Mock database session
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with pytest.raises(Exception) as exc_info:
            await enhanced_service.send_contextual_notification(
                user_id=1,
                context="unknown_context",
                context_data={},
                db=mock_db
            )
        
        assert "Unknown context" in str(exc_info.value) 