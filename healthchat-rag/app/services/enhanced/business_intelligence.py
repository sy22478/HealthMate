"""
Business Intelligence System for HealthMate
Advanced analytics infrastructure for aggregated health metrics, user engagement, and system performance
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from collections import defaultdict
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc, text
from sqlalchemy.dialects.postgresql import ARRAY

from app.database import get_db
from app.models.enhanced_health_models import UserHealthProfile, HealthMetricsAggregation, ConversationHistory
from app.models.user import User
from app.models.notification_models import Notification, NotificationDeliveryAttempt
from app.exceptions.health_exceptions import BusinessIntelligenceError
from app.utils.encryption_utils import field_encryption
from app.utils.performance_monitoring import monitor_custom_performance

logger = logging.getLogger(__name__)

class MetricType(str, Enum):
    """Types of business intelligence metrics"""
    HEALTH_METRICS = "health_metrics"
    USER_ENGAGEMENT = "user_engagement"
    SYSTEM_PERFORMANCE = "system_performance"
    FINANCIAL_METRICS = "financial_metrics"
    OPERATIONAL_METRICS = "operational_metrics"

class AggregationPeriod(str, Enum):
    """Aggregation periods for metrics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class ReportType(str, Enum):
    """Types of automated reports"""
    HEALTH_SUMMARY = "health_summary"
    USER_ENGAGEMENT = "user_engagement"
    SYSTEM_PERFORMANCE = "system_performance"
    COMPLIANCE = "compliance"
    FINANCIAL = "financial"
    OPERATIONAL = "operational"

@dataclass
class AggregatedHealthMetrics:
    """Aggregated health metrics for business intelligence"""
    user_id: int
    aggregation_period: AggregationPeriod
    period_start: datetime
    period_end: datetime
    
    # Health metrics
    avg_blood_pressure_systolic: Optional[float] = None
    avg_blood_pressure_diastolic: Optional[float] = None
    avg_heart_rate: Optional[float] = None
    avg_weight: Optional[float] = None
    avg_blood_sugar: Optional[float] = None
    avg_temperature: Optional[float] = None
    
    # Activity metrics
    total_steps: Optional[int] = None
    total_calories_burned: Optional[float] = None
    total_exercise_minutes: Optional[int] = None
    
    # Sleep metrics
    avg_sleep_hours: Optional[float] = None
    sleep_quality_score: Optional[float] = None
    
    # Medication adherence
    medication_adherence_rate: Optional[float] = None
    total_medications_taken: Optional[int] = None
    missed_doses: Optional[int] = None
    
    # Health score
    overall_health_score: Optional[float] = None
    health_score_trend: Optional[float] = None
    
    # Data quality
    data_completeness: Optional[float] = None
    data_accuracy: Optional[float] = None
    source_count: Optional[int] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class UserEngagementMetrics:
    """User engagement analytics for business intelligence"""
    user_id: int
    date: datetime
    
    # Login metrics
    login_count: int = 0
    session_duration_minutes: int = 0
    total_sessions: int = 0
    
    # Feature usage
    features_used: List[str] = field(default_factory=list)
    health_data_points_added: int = 0
    chat_messages_sent: int = 0
    notifications_received: int = 0
    
    # Engagement scores
    engagement_score: Optional[float] = None
    feature_adoption_rate: Optional[float] = None
    retention_score: Optional[float] = None
    
    # User behavior
    time_spent_in_app_minutes: int = 0
    pages_visited: List[str] = field(default_factory=list)
    actions_performed: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class SystemPerformanceMetrics:
    """System performance metrics for business intelligence"""
    metric_name: str
    metric_value: float
    metric_unit: str
    timestamp: datetime
    
    # Service information
    service_name: str
    environment: str
    instance_id: Optional[str] = None
    
    # Performance context
    response_time_ms: Optional[float] = None
    error_rate: Optional[float] = None
    throughput: Optional[float] = None
    resource_usage: Optional[Dict[str, float]] = None
    
    # Metadata
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class BusinessIntelligenceReport:
    """Business intelligence report structure"""
    report_id: str
    report_type: ReportType
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    
    # Report content
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    insights: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    
    # Report metadata
    generated_by: str
    data_sources: List[str]
    confidence_score: float
    report_format: str = "json"
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)

class BusinessIntelligenceService:
    """Main business intelligence service"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = self._load_bi_config()
    
    def _load_bi_config(self) -> Dict[str, Any]:
        """Load business intelligence configuration"""
        return {
            'aggregation_schedules': {
                'health_metrics': {
                    'hourly': True,
                    'daily': True,
                    'weekly': True,
                    'monthly': True
                },
                'user_engagement': {
                    'daily': True,
                    'weekly': True,
                    'monthly': True
                },
                'system_performance': {
                    'hourly': True,
                    'daily': True
                }
            },
            'report_schedules': {
                'health_summary': 'daily',
                'user_engagement': 'weekly',
                'system_performance': 'daily',
                'compliance': 'monthly',
                'financial': 'monthly',
                'operational': 'weekly'
            },
            'data_retention': {
                'hourly_metrics': 30,  # days
                'daily_metrics': 365,  # days
                'weekly_metrics': 104,  # weeks
                'monthly_metrics': 60,  # months
                'reports': 2555  # days (7 years)
            },
            'performance_thresholds': {
                'response_time_ms': 200,
                'error_rate': 0.01,
                'uptime_percentage': 99.9
            }
        }
    
    @monitor_custom_performance("create_aggregated_health_metrics_tables")
    async def create_aggregated_health_metrics_tables(self) -> Dict[str, Any]:
        """Create comprehensive aggregated health metrics tables"""
        try:
            # Create enhanced aggregated health metrics table
            health_metrics_table = """
            CREATE TABLE IF NOT EXISTS bi_aggregated_health_metrics (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                aggregation_period VARCHAR(20) NOT NULL,
                period_start TIMESTAMP NOT NULL,
                period_end TIMESTAMP NOT NULL,
                
                -- Health metrics
                avg_blood_pressure_systolic DECIMAL(5,2),
                avg_blood_pressure_diastolic DECIMAL(5,2),
                min_blood_pressure_systolic DECIMAL(5,2),
                max_blood_pressure_systolic DECIMAL(5,2),
                min_blood_pressure_diastolic DECIMAL(5,2),
                max_blood_pressure_diastolic DECIMAL(5,2),
                
                avg_heart_rate DECIMAL(5,2),
                min_heart_rate DECIMAL(5,2),
                max_heart_rate DECIMAL(5,2),
                resting_heart_rate DECIMAL(5,2),
                
                avg_weight DECIMAL(6,2),
                weight_change DECIMAL(6,2),
                bmi_trend DECIMAL(4,2),
                
                avg_blood_sugar DECIMAL(5,2),
                min_blood_sugar DECIMAL(5,2),
                max_blood_sugar DECIMAL(5,2),
                
                avg_temperature DECIMAL(4,2),
                min_temperature DECIMAL(4,2),
                max_temperature DECIMAL(4,2),
                
                -- Activity metrics
                total_steps INTEGER,
                avg_steps_per_day DECIMAL(8,2),
                total_calories_burned DECIMAL(8,2),
                avg_calories_burned_per_day DECIMAL(8,2),
                total_exercise_minutes INTEGER,
                avg_exercise_minutes_per_day DECIMAL(6,2),
                
                -- Sleep metrics
                avg_sleep_hours DECIMAL(4,2),
                total_sleep_hours DECIMAL(8,2),
                sleep_quality_score DECIMAL(5,2),
                
                -- Medication adherence
                medication_adherence_rate DECIMAL(5,2),
                total_medications_taken INTEGER,
                total_medications_scheduled INTEGER,
                missed_doses INTEGER,
                
                -- Symptom tracking
                total_symptoms_logged INTEGER,
                avg_symptom_severity DECIMAL(4,2),
                most_common_symptom VARCHAR(200),
                symptom_frequency JSONB,
                
                -- Health score
                overall_health_score DECIMAL(5,2),
                health_score_trend DECIMAL(5,2),
                
                -- Data quality
                data_completeness DECIMAL(3,2),
                data_accuracy DECIMAL(3,2),
                source_count INTEGER,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Indexes
                CONSTRAINT fk_bi_health_metrics_user FOREIGN KEY (user_id) REFERENCES users(id),
                CONSTRAINT uk_bi_health_metrics_period UNIQUE (user_id, aggregation_period, period_start)
            );
            """
            
            # Create user engagement analytics table
            engagement_table = """
            CREATE TABLE IF NOT EXISTS bi_user_engagement_analytics (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                
                -- Login metrics
                login_count INTEGER DEFAULT 0,
                session_duration_minutes INTEGER DEFAULT 0,
                total_sessions INTEGER DEFAULT 0,
                avg_session_duration_minutes DECIMAL(6,2),
                
                -- Feature usage
                features_used TEXT[],
                health_data_points_added INTEGER DEFAULT 0,
                chat_messages_sent INTEGER DEFAULT 0,
                notifications_received INTEGER DEFAULT 0,
                
                -- Engagement scores
                engagement_score DECIMAL(5,2),
                feature_adoption_rate DECIMAL(5,2),
                retention_score DECIMAL(5,2),
                
                -- User behavior
                time_spent_in_app_minutes INTEGER DEFAULT 0,
                pages_visited TEXT[],
                actions_performed INTEGER DEFAULT 0,
                
                -- Feature-specific metrics
                health_data_entries INTEGER DEFAULT 0,
                medication_logs INTEGER DEFAULT 0,
                symptom_logs INTEGER DEFAULT 0,
                goal_achievements INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Indexes
                CONSTRAINT fk_bi_engagement_user FOREIGN KEY (user_id) REFERENCES users(id),
                CONSTRAINT uk_bi_engagement_date UNIQUE (user_id, date)
            );
            """
            
            # Create system performance metrics table
            performance_table = """
            CREATE TABLE IF NOT EXISTS bi_system_performance_metrics (
                id SERIAL PRIMARY KEY,
                metric_name VARCHAR(100) NOT NULL,
                metric_value DECIMAL(10,2),
                metric_unit VARCHAR(20),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                -- Service information
                service_name VARCHAR(50),
                environment VARCHAR(20),
                instance_id VARCHAR(100),
                
                -- Performance context
                response_time_ms DECIMAL(8,2),
                error_rate DECIMAL(5,4),
                throughput DECIMAL(10,2),
                resource_usage JSONB,
                
                -- Metadata
                tags JSONB,
                
                -- Indexes
                INDEX idx_bi_performance_timestamp (timestamp),
                INDEX idx_bi_performance_service (service_name, timestamp)
            );
            """
            
            # Execute table creation
            with self.db.begin():
                self.db.execute(text(health_metrics_table))
                self.db.execute(text(engagement_table))
                self.db.execute(text(performance_table))
            
            logger.info("Business intelligence tables created successfully")
            return {
                "success": True,
                "tables_created": [
                    "bi_aggregated_health_metrics",
                    "bi_user_engagement_analytics", 
                    "bi_system_performance_metrics"
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating BI tables: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to create BI tables: {str(e)}")
    
    @monitor_custom_performance("aggregate_health_metrics")
    async def aggregate_health_metrics(self, user_id: int, period: AggregationPeriod, 
                                     start_date: datetime, end_date: datetime) -> AggregatedHealthMetrics:
        """Aggregate health metrics for business intelligence"""
        try:
            # Get health metrics aggregation from existing table
            aggregations = self.db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.health_profile_id == user_id,
                    HealthMetricsAggregation.aggregation_period == period.value,
                    HealthMetricsAggregation.period_start >= start_date,
                    HealthMetricsAggregation.period_end <= end_date
                )
            ).all()
            
            if not aggregations:
                logger.warning(f"No health metrics found for user {user_id} in period {period}")
                return None
            
            # Calculate aggregated metrics
            aggregated = AggregatedHealthMetrics(
                user_id=user_id,
                aggregation_period=period,
                period_start=start_date,
                period_end=end_date
            )
            
            # Aggregate health metrics
            aggregated.avg_blood_pressure_systolic = np.mean([
                agg.avg_blood_pressure_systolic for agg in aggregations 
                if agg.avg_blood_pressure_systolic is not None
            ]) if any(agg.avg_blood_pressure_systolic for agg in aggregations) else None
            
            aggregated.avg_blood_pressure_diastolic = np.mean([
                agg.avg_blood_pressure_diastolic for agg in aggregations 
                if agg.avg_blood_pressure_diastolic is not None
            ]) if any(agg.avg_blood_pressure_diastolic for agg in aggregations) else None
            
            aggregated.avg_heart_rate = np.mean([
                agg.avg_heart_rate for agg in aggregations 
                if agg.avg_heart_rate is not None
            ]) if any(agg.avg_heart_rate for agg in aggregations) else None
            
            aggregated.avg_weight = np.mean([
                agg.avg_weight for agg in aggregations 
                if agg.avg_weight is not None
            ]) if any(agg.avg_weight for agg in aggregations) else None
            
            # Aggregate activity metrics
            aggregated.total_steps = sum([
                agg.total_steps for agg in aggregations 
                if agg.total_steps is not None
            ])
            
            aggregated.total_calories_burned = sum([
                agg.total_calories_burned for agg in aggregations 
                if agg.total_calories_burned is not None
            ])
            
            aggregated.total_exercise_minutes = sum([
                agg.total_exercise_minutes for agg in aggregations 
                if agg.total_exercise_minutes is not None
            ])
            
            # Aggregate sleep metrics
            aggregated.avg_sleep_hours = np.mean([
                agg.avg_sleep_hours for agg in aggregations 
                if agg.avg_sleep_hours is not None
            ]) if any(agg.avg_sleep_hours for agg in aggregations) else None
            
            aggregated.sleep_quality_score = np.mean([
                agg.sleep_quality_score for agg in aggregations 
                if agg.sleep_quality_score is not None
            ]) if any(agg.sleep_quality_score for agg in aggregations) else None
            
            # Aggregate medication adherence
            adherence_rates = [
                agg.medication_adherence_rate for agg in aggregations 
                if agg.medication_adherence_rate is not None
            ]
            aggregated.medication_adherence_rate = np.mean(adherence_rates) if adherence_rates else None
            
            aggregated.total_medications_taken = sum([
                agg.total_medications_taken for agg in aggregations 
                if agg.total_medications_taken is not None
            ])
            
            aggregated.missed_doses = sum([
                agg.missed_doses for agg in aggregations 
                if agg.missed_doses is not None
            ])
            
            # Calculate health score trend
            health_scores = [
                agg.overall_health_score for agg in aggregations 
                if agg.overall_health_score is not None
            ]
            if len(health_scores) >= 2:
                aggregated.overall_health_score = np.mean(health_scores)
                aggregated.health_score_trend = health_scores[-1] - health_scores[0]
            
            # Calculate data quality metrics
            aggregated.data_completeness = self._calculate_data_completeness(aggregations)
            aggregated.source_count = len(set([
                agg.health_profile_id for agg in aggregations
            ]))
            
            return aggregated
            
        except Exception as e:
            logger.error(f"Error aggregating health metrics: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to aggregate health metrics: {str(e)}")
    
    @monitor_custom_performance("track_user_engagement")
    async def track_user_engagement(self, user_id: int, date: datetime) -> UserEngagementMetrics:
        """Track user engagement metrics for business intelligence"""
        try:
            # Get user activity for the date
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # Get login sessions (simulated - in real implementation, this would come from session logs)
            login_count = 1  # Placeholder
            session_duration_minutes = 45  # Placeholder
            total_sessions = 2  # Placeholder
            
            # Get feature usage from conversation history
            chat_messages = self.db.query(ConversationHistory).filter(
                and_(
                    ConversationHistory.user_id == user_id,
                    ConversationHistory.created_at >= start_of_day,
                    ConversationHistory.created_at < end_of_day
                )
            ).count()
            
            # Get notifications received
            notifications_received = self.db.query(Notification).filter(
                and_(
                    Notification.user_id == user_id,
                    Notification.created_at >= start_of_day,
                    Notification.created_at < end_of_day
                )
            ).count()
            
            # Calculate engagement metrics
            engagement_metrics = UserEngagementMetrics(
                user_id=user_id,
                date=date,
                login_count=login_count,
                session_duration_minutes=session_duration_minutes,
                total_sessions=total_sessions,
                chat_messages_sent=chat_messages,
                notifications_received=notifications_received,
                features_used=["chat", "health_tracking", "notifications"],
                health_data_points_added=5,  # Placeholder
                engagement_score=self._calculate_engagement_score(login_count, session_duration_minutes, chat_messages),
                feature_adoption_rate=0.75,  # Placeholder
                retention_score=0.85,  # Placeholder
                time_spent_in_app_minutes=session_duration_minutes,
                pages_visited=["dashboard", "health_metrics", "chat"],
                actions_performed=chat_messages + notifications_received + 5
            )
            
            return engagement_metrics
            
        except Exception as e:
            logger.error(f"Error tracking user engagement: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to track user engagement: {str(e)}")
    
    @monitor_custom_performance("collect_system_performance_metrics")
    async def collect_system_performance_metrics(self, service_name: str, 
                                               environment: str = "production") -> SystemPerformanceMetrics:
        """Collect system performance metrics for business intelligence"""
        try:
            # In a real implementation, this would collect actual system metrics
            # For now, we'll create sample metrics
            
            performance_metrics = SystemPerformanceMetrics(
                metric_name="api_response_time",
                metric_value=150.5,
                metric_unit="ms",
                timestamp=datetime.utcnow(),
                service_name=service_name,
                environment=environment,
                instance_id="instance-123",
                response_time_ms=150.5,
                error_rate=0.005,
                throughput=1000.0,
                resource_usage={
                    "cpu_percent": 45.2,
                    "memory_percent": 62.8,
                    "disk_usage_percent": 23.1
                },
                tags={
                    "service": service_name,
                    "environment": environment,
                    "version": "1.0.0"
                }
            )
            
            return performance_metrics
            
        except Exception as e:
            logger.error(f"Error collecting system performance metrics: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to collect system performance metrics: {str(e)}")
    
    @monitor_custom_performance("generate_automated_report")
    async def generate_automated_report(self, report_type: ReportType, 
                                      start_date: datetime, end_date: datetime,
                                      generated_by: str = "system") -> BusinessIntelligenceReport:
        """Generate automated business intelligence report"""
        try:
            report_id = f"bi_report_{report_type.value}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            
            if report_type == ReportType.HEALTH_SUMMARY:
                report = await self._generate_health_summary_report(report_id, start_date, end_date, generated_by)
            elif report_type == ReportType.USER_ENGAGEMENT:
                report = await self._generate_user_engagement_report(report_id, start_date, end_date, generated_by)
            elif report_type == ReportType.SYSTEM_PERFORMANCE:
                report = await self._generate_system_performance_report(report_id, start_date, end_date, generated_by)
            else:
                raise BusinessIntelligenceError(f"Unsupported report type: {report_type}")
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating automated report: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to generate automated report: {str(e)}")
    
    async def _generate_health_summary_report(self, report_id: str, start_date: datetime, 
                                            end_date: datetime, generated_by: str) -> BusinessIntelligenceReport:
        """Generate health summary report"""
        try:
            # Get health metrics for the period
            health_metrics = self.db.query(HealthMetricsAggregation).filter(
                and_(
                    HealthMetricsAggregation.period_start >= start_date,
                    HealthMetricsAggregation.period_end <= end_date
                )
            ).all()
            
            # Calculate summary metrics
            total_users = len(set(agg.health_profile_id for agg in health_metrics))
            avg_health_score = np.mean([
                agg.overall_health_score for agg in health_metrics 
                if agg.overall_health_score is not None
            ]) if health_metrics else 0
            
            # Generate insights
            insights = [
                {
                    "type": "health_trend",
                    "title": "Average Health Score Trend",
                    "description": f"Average health score across {total_users} users: {avg_health_score:.2f}",
                    "value": avg_health_score,
                    "trend": "stable"
                }
            ]
            
            # Generate recommendations
            recommendations = [
                {
                    "type": "data_quality",
                    "title": "Improve Data Completeness",
                    "description": "Focus on increasing data completeness for better health insights",
                    "priority": "medium"
                }
            ]
            
            return BusinessIntelligenceReport(
                report_id=report_id,
                report_type=ReportType.HEALTH_SUMMARY,
                generated_at=datetime.utcnow(),
                period_start=start_date,
                period_end=end_date,
                summary={
                    "total_users": total_users,
                    "avg_health_score": avg_health_score,
                    "data_points_analyzed": len(health_metrics)
                },
                metrics={
                    "health_scores": [agg.overall_health_score for agg in health_metrics if agg.overall_health_score],
                    "medication_adherence": [agg.medication_adherence_rate for agg in health_metrics if agg.medication_adherence_rate]
                },
                insights=insights,
                recommendations=recommendations,
                generated_by=generated_by,
                data_sources=["health_metrics_aggregation"],
                confidence_score=0.85
            )
            
        except Exception as e:
            logger.error(f"Error generating health summary report: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to generate health summary report: {str(e)}")
    
    async def _generate_user_engagement_report(self, report_id: str, start_date: datetime,
                                             end_date: datetime, generated_by: str) -> BusinessIntelligenceReport:
        """Generate user engagement report"""
        try:
            # Get user engagement data (simulated)
            total_users = 1000
            avg_engagement_score = 0.75
            avg_session_duration = 45
            
            insights = [
                {
                    "type": "engagement_trend",
                    "title": "User Engagement Stable",
                    "description": f"Average engagement score: {avg_engagement_score:.2f}",
                    "value": avg_engagement_score,
                    "trend": "stable"
                }
            ]
            
            recommendations = [
                {
                    "type": "feature_adoption",
                    "title": "Increase Feature Adoption",
                    "description": "Focus on onboarding users to advanced features",
                    "priority": "high"
                }
            ]
            
            return BusinessIntelligenceReport(
                report_id=report_id,
                report_type=ReportType.USER_ENGAGEMENT,
                generated_at=datetime.utcnow(),
                period_start=start_date,
                period_end=end_date,
                summary={
                    "total_users": total_users,
                    "avg_engagement_score": avg_engagement_score,
                    "avg_session_duration": avg_session_duration
                },
                metrics={
                    "engagement_scores": [0.75, 0.78, 0.72, 0.76, 0.74],
                    "session_durations": [45, 52, 38, 47, 43]
                },
                insights=insights,
                recommendations=recommendations,
                generated_by=generated_by,
                data_sources=["user_engagement_analytics"],
                confidence_score=0.80
            )
            
        except Exception as e:
            logger.error(f"Error generating user engagement report: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to generate user engagement report: {str(e)}")
    
    async def _generate_system_performance_report(self, report_id: str, start_date: datetime,
                                                end_date: datetime, generated_by: str) -> BusinessIntelligenceReport:
        """Generate system performance report"""
        try:
            # Get system performance data (simulated)
            avg_response_time = 150.5
            error_rate = 0.005
            uptime_percentage = 99.95
            
            insights = [
                {
                    "type": "performance",
                    "title": "System Performance Excellent",
                    "description": f"Average response time: {avg_response_time}ms",
                    "value": avg_response_time,
                    "trend": "improving"
                }
            ]
            
            recommendations = [
                {
                    "type": "optimization",
                    "title": "Monitor Database Performance",
                    "description": "Consider database optimization for better response times",
                    "priority": "low"
                }
            ]
            
            return BusinessIntelligenceReport(
                report_id=report_id,
                report_type=ReportType.SYSTEM_PERFORMANCE,
                generated_at=datetime.utcnow(),
                period_start=start_date,
                period_end=end_date,
                summary={
                    "avg_response_time": avg_response_time,
                    "error_rate": error_rate,
                    "uptime_percentage": uptime_percentage
                },
                metrics={
                    "response_times": [150, 145, 155, 148, 152],
                    "error_rates": [0.005, 0.003, 0.007, 0.004, 0.006]
                },
                insights=insights,
                recommendations=recommendations,
                generated_by=generated_by,
                data_sources=["system_performance_metrics"],
                confidence_score=0.90
            )
            
        except Exception as e:
            logger.error(f"Error generating system performance report: {str(e)}")
            raise BusinessIntelligenceError(f"Failed to generate system performance report: {str(e)}")
    
    def _calculate_data_completeness(self, aggregations: List[HealthMetricsAggregation]) -> float:
        """Calculate data completeness score"""
        if not aggregations:
            return 0.0
        
        total_fields = 0
        filled_fields = 0
        
        for agg in aggregations:
            # Count health metric fields
            fields = [
                agg.avg_blood_pressure_systolic, agg.avg_heart_rate, agg.avg_weight,
                agg.total_steps, agg.avg_sleep_hours, agg.medication_adherence_rate
            ]
            
            total_fields += len(fields)
            filled_fields += sum(1 for field in fields if field is not None)
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _calculate_engagement_score(self, login_count: int, session_duration: int, 
                                  chat_messages: int) -> float:
        """Calculate user engagement score"""
        # Simple engagement scoring algorithm
        login_score = min(login_count / 3.0, 1.0)  # Cap at 3 logins per day
        duration_score = min(session_duration / 60.0, 1.0)  # Cap at 60 minutes
        activity_score = min(chat_messages / 10.0, 1.0)  # Cap at 10 messages
        
        # Weighted average
        engagement_score = (login_score * 0.4 + duration_score * 0.4 + activity_score * 0.2)
        return round(engagement_score, 2)

# Factory function for creating BI service
def get_business_intelligence_service(db_session: Session) -> BusinessIntelligenceService:
    """Get business intelligence service instance"""
    return BusinessIntelligenceService(db_session)

# Global instance for background tasks
business_intelligence_service = None

def get_global_bi_service() -> BusinessIntelligenceService:
    """Get global business intelligence service instance"""
    global business_intelligence_service
    if business_intelligence_service is None:
        db = next(get_db())
        business_intelligence_service = BusinessIntelligenceService(db)
    return business_intelligence_service 