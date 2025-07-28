"""
Tests for Business Intelligence System
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from app.services.enhanced.business_intelligence import (
    BusinessIntelligenceService, MetricType, AggregationPeriod, ReportType,
    AggregatedHealthMetrics, UserEngagementMetrics, SystemPerformanceMetrics,
    BusinessIntelligenceReport, get_business_intelligence_service
)
from app.exceptions.health_exceptions import BusinessIntelligenceError
from app.models.enhanced_health_models import HealthMetricsAggregation, UserHealthProfile
from app.models.user import User

class TestBusinessIntelligenceService:
    """Test cases for BusinessIntelligenceService"""
    
    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def bi_service(self, mock_db_session):
        """Business intelligence service instance"""
        return BusinessIntelligenceService(mock_db_session)
    
    @pytest.fixture
    def sample_health_metrics_aggregation(self):
        """Sample health metrics aggregation data"""
        return HealthMetricsAggregation(
            id=1,
            health_profile_id=1,
            aggregation_period="daily",
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 2),
            avg_blood_pressure_systolic=120.0,
            avg_blood_pressure_diastolic=80.0,
            avg_heart_rate=72.0,
            avg_weight=70.0,
            total_steps=8000,
            total_calories_burned=2000.0,
            total_exercise_minutes=45,
            avg_sleep_hours=7.5,
            sleep_quality_score=85.0,
            medication_adherence_rate=95.0,
            total_medications_taken=10,
            missed_doses=1,
            overall_health_score=82.0
        )
    
    def test_bi_service_initialization(self, bi_service):
        """Test business intelligence service initialization"""
        assert bi_service is not None
        assert hasattr(bi_service, 'config')
        assert 'aggregation_schedules' in bi_service.config
        assert 'report_schedules' in bi_service.config
        assert 'data_retention' in bi_service.config
    
    def test_load_bi_config(self, bi_service):
        """Test BI configuration loading"""
        config = bi_service._load_bi_config()
        
        assert 'aggregation_schedules' in config
        assert 'report_schedules' in config
        assert 'data_retention' in config
        assert 'performance_thresholds' in config
        
        # Check aggregation schedules
        assert 'health_metrics' in config['aggregation_schedules']
        assert 'user_engagement' in config['aggregation_schedules']
        assert 'system_performance' in config['aggregation_schedules']
        
        # Check report schedules
        assert 'health_summary' in config['report_schedules']
        assert 'user_engagement' in config['report_schedules']
        assert 'system_performance' in config['report_schedules']
    
    @pytest.mark.asyncio
    async def test_create_aggregated_health_metrics_tables(self, bi_service):
        """Test creating aggregated health metrics tables"""
        with patch.object(bi_service.db, 'begin') as mock_begin:
            with patch.object(bi_service.db, 'execute') as mock_execute:
                mock_begin.return_value.__enter__ = Mock()
                mock_begin.return_value.__exit__ = Mock(return_value=None)
                
                result = await bi_service.create_aggregated_health_metrics_tables()
                
                assert result['success'] is True
                assert 'tables_created' in result
                assert len(result['tables_created']) == 3
                assert 'bi_aggregated_health_metrics' in result['tables_created']
                assert 'bi_user_engagement_analytics' in result['tables_created']
                assert 'bi_system_performance_metrics' in result['tables_created']
                
                # Verify SQL execution was called
                assert mock_execute.call_count == 3
    
    @pytest.mark.asyncio
    async def test_aggregate_health_metrics(self, bi_service, sample_health_metrics_aggregation):
        """Test aggregating health metrics"""
        # Mock database query
        bi_service.db.query.return_value.filter.return_value.all.return_value = [sample_health_metrics_aggregation]
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        result = await bi_service.aggregate_health_metrics(
            user_id=1,
            period=AggregationPeriod.DAILY,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is not None
        assert result.user_id == 1
        assert result.aggregation_period == AggregationPeriod.DAILY
        assert result.period_start == start_date
        assert result.period_end == end_date
        assert result.avg_blood_pressure_systolic == 120.0
        assert result.avg_heart_rate == 72.0
        assert result.total_steps == 8000
        assert result.medication_adherence_rate == 95.0
    
    @pytest.mark.asyncio
    async def test_aggregate_health_metrics_no_data(self, bi_service):
        """Test aggregating health metrics with no data"""
        # Mock empty database query
        bi_service.db.query.return_value.filter.return_value.all.return_value = []
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 2)
        
        result = await bi_service.aggregate_health_metrics(
            user_id=1,
            period=AggregationPeriod.DAILY,
            start_date=start_date,
            end_date=end_date
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_track_user_engagement(self, bi_service):
        """Test tracking user engagement metrics"""
        # Mock database queries
        bi_service.db.query.return_value.filter.return_value.count.return_value = 5
        
        date = datetime(2024, 1, 1)
        
        result = await bi_service.track_user_engagement(
            user_id=1,
            date=date
        )
        
        assert result is not None
        assert result.user_id == 1
        assert result.date == date
        assert result.chat_messages_sent == 5
        assert result.notifications_received == 5
        assert result.engagement_score is not None
        assert result.features_used == ["chat", "health_tracking", "notifications"]
    
    @pytest.mark.asyncio
    async def test_collect_system_performance_metrics(self, bi_service):
        """Test collecting system performance metrics"""
        result = await bi_service.collect_system_performance_metrics(
            service_name="api",
            environment="production"
        )
        
        assert result is not None
        assert result.metric_name == "api_response_time"
        assert result.service_name == "api"
        assert result.environment == "production"
        assert result.response_time_ms == 150.5
        assert result.error_rate == 0.005
        assert result.throughput == 1000.0
        assert result.resource_usage is not None
        assert "cpu_percent" in result.resource_usage
    
    @pytest.mark.asyncio
    async def test_generate_health_summary_report(self, bi_service, sample_health_metrics_aggregation):
        """Test generating health summary report"""
        # Mock database query
        bi_service.db.query.return_value.filter.return_value.all.return_value = [sample_health_metrics_aggregation]
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        result = await bi_service._generate_health_summary_report(
            report_id="test_report",
            start_date=start_date,
            end_date=end_date,
            generated_by="test_user"
        )
        
        assert result is not None
        assert result.report_id == "test_report"
        assert result.report_type == ReportType.HEALTH_SUMMARY
        assert result.period_start == start_date
        assert result.period_end == end_date
        assert result.generated_by == "test_user"
        assert result.summary is not None
        assert result.insights is not None
        assert result.recommendations is not None
        assert result.confidence_score == 0.85
    
    @pytest.mark.asyncio
    async def test_generate_user_engagement_report(self, bi_service):
        """Test generating user engagement report"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        result = await bi_service._generate_user_engagement_report(
            report_id="test_report",
            start_date=start_date,
            end_date=end_date,
            generated_by="test_user"
        )
        
        assert result is not None
        assert result.report_id == "test_report"
        assert result.report_type == ReportType.USER_ENGAGEMENT
        assert result.period_start == start_date
        assert result.period_end == end_date
        assert result.generated_by == "test_user"
        assert result.summary is not None
        assert result.insights is not None
        assert result.recommendations is not None
        assert result.confidence_score == 0.80
    
    @pytest.mark.asyncio
    async def test_generate_system_performance_report(self, bi_service):
        """Test generating system performance report"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        result = await bi_service._generate_system_performance_report(
            report_id="test_report",
            start_date=start_date,
            end_date=end_date,
            generated_by="test_user"
        )
        
        assert result is not None
        assert result.report_id == "test_report"
        assert result.report_type == ReportType.SYSTEM_PERFORMANCE
        assert result.period_start == start_date
        assert result.period_end == end_date
        assert result.generated_by == "test_user"
        assert result.summary is not None
        assert result.insights is not None
        assert result.recommendations is not None
        assert result.confidence_score == 0.90
    
    @pytest.mark.asyncio
    async def test_generate_automated_report(self, bi_service):
        """Test generating automated report"""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 7)
        
        # Test health summary report
        with patch.object(bi_service, '_generate_health_summary_report') as mock_generate:
            mock_generate.return_value = Mock(spec=BusinessIntelligenceReport)
            
            result = await bi_service.generate_automated_report(
                report_type=ReportType.HEALTH_SUMMARY,
                start_date=start_date,
                end_date=end_date,
                generated_by="test_user"
            )
            
            assert result is not None
            mock_generate.assert_called_once()
        
        # Test unsupported report type
        with pytest.raises(BusinessIntelligenceError):
            await bi_service.generate_automated_report(
                report_type="unsupported_type",  # type: ignore
                start_date=start_date,
                end_date=end_date,
                generated_by="test_user"
            )
    
    def test_calculate_data_completeness(self, bi_service, sample_health_metrics_aggregation):
        """Test calculating data completeness"""
        # Test with complete data
        completeness = bi_service._calculate_data_completeness([sample_health_metrics_aggregation])
        assert completeness > 0.0
        assert completeness <= 1.0
        
        # Test with empty data
        completeness = bi_service._calculate_data_completeness([])
        assert completeness == 0.0
    
    def test_calculate_engagement_score(self, bi_service):
        """Test calculating engagement score"""
        # Test normal engagement
        score = bi_service._calculate_engagement_score(
            login_count=2,
            session_duration=45,
            chat_messages=5
        )
        assert score > 0.0
        assert score <= 1.0
        
        # Test high engagement
        score = bi_service._calculate_engagement_score(
            login_count=5,
            session_duration=90,
            chat_messages=15
        )
        assert score > 0.0
        assert score <= 1.0
        
        # Test low engagement
        score = bi_service._calculate_engagement_score(
            login_count=1,
            session_duration=10,
            chat_messages=1
        )
        assert score > 0.0
        assert score <= 1.0

class TestBusinessIntelligenceDataClasses:
    """Test cases for business intelligence data classes"""
    
    def test_aggregated_health_metrics(self):
        """Test AggregatedHealthMetrics data class"""
        metrics = AggregatedHealthMetrics(
            user_id=1,
            aggregation_period=AggregationPeriod.DAILY,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 2),
            avg_blood_pressure_systolic=120.0,
            avg_heart_rate=72.0,
            total_steps=8000
        )
        
        assert metrics.user_id == 1
        assert metrics.aggregation_period == AggregationPeriod.DAILY
        assert metrics.avg_blood_pressure_systolic == 120.0
        assert metrics.avg_heart_rate == 72.0
        assert metrics.total_steps == 8000
        assert metrics.created_at is not None
        assert metrics.updated_at is not None
    
    def test_user_engagement_metrics(self):
        """Test UserEngagementMetrics data class"""
        engagement = UserEngagementMetrics(
            user_id=1,
            date=datetime(2024, 1, 1),
            login_count=2,
            session_duration_minutes=45,
            chat_messages_sent=5,
            engagement_score=0.75
        )
        
        assert engagement.user_id == 1
        assert engagement.date == datetime(2024, 1, 1)
        assert engagement.login_count == 2
        assert engagement.session_duration_minutes == 45
        assert engagement.chat_messages_sent == 5
        assert engagement.engagement_score == 0.75
        assert engagement.created_at is not None
    
    def test_system_performance_metrics(self):
        """Test SystemPerformanceMetrics data class"""
        performance = SystemPerformanceMetrics(
            metric_name="api_response_time",
            metric_value=150.5,
            metric_unit="ms",
            timestamp=datetime(2024, 1, 1),
            service_name="api",
            environment="production",
            response_time_ms=150.5,
            error_rate=0.005
        )
        
        assert performance.metric_name == "api_response_time"
        assert performance.metric_value == 150.5
        assert performance.metric_unit == "ms"
        assert performance.service_name == "api"
        assert performance.environment == "production"
        assert performance.response_time_ms == 150.5
        assert performance.error_rate == 0.005
        assert performance.created_at is not None
    
    def test_business_intelligence_report(self):
        """Test BusinessIntelligenceReport data class"""
        report = BusinessIntelligenceReport(
            report_id="test_report",
            report_type=ReportType.HEALTH_SUMMARY,
            generated_at=datetime(2024, 1, 1),
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 7),
            summary={"total_users": 1000},
            metrics={"health_scores": [80, 85, 90]},
            insights=[{"type": "trend", "title": "Improving"}],
            recommendations=[{"type": "action", "title": "Continue"}],
            generated_by="test_user",
            data_sources=["health_metrics"],
            confidence_score=0.85
        )
        
        assert report.report_id == "test_report"
        assert report.report_type == ReportType.HEALTH_SUMMARY
        assert report.generated_by == "test_user"
        assert report.confidence_score == 0.85
        assert len(report.insights) == 1
        assert len(report.recommendations) == 1
        assert report.created_at is not None

class TestBusinessIntelligenceEnums:
    """Test cases for business intelligence enums"""
    
    def test_metric_type_enum(self):
        """Test MetricType enum"""
        assert MetricType.HEALTH_METRICS == "health_metrics"
        assert MetricType.USER_ENGAGEMENT == "user_engagement"
        assert MetricType.SYSTEM_PERFORMANCE == "system_performance"
        assert MetricType.FINANCIAL_METRICS == "financial_metrics"
        assert MetricType.OPERATIONAL_METRICS == "operational_metrics"
    
    def test_aggregation_period_enum(self):
        """Test AggregationPeriod enum"""
        assert AggregationPeriod.HOURLY == "hourly"
        assert AggregationPeriod.DAILY == "daily"
        assert AggregationPeriod.WEEKLY == "weekly"
        assert AggregationPeriod.MONTHLY == "monthly"
        assert AggregationPeriod.QUARTERLY == "quarterly"
        assert AggregationPeriod.YEARLY == "yearly"
    
    def test_report_type_enum(self):
        """Test ReportType enum"""
        assert ReportType.HEALTH_SUMMARY == "health_summary"
        assert ReportType.USER_ENGAGEMENT == "user_engagement"
        assert ReportType.SYSTEM_PERFORMANCE == "system_performance"
        assert ReportType.COMPLIANCE == "compliance"
        assert ReportType.FINANCIAL == "financial"
        assert ReportType.OPERATIONAL == "operational"

class TestBusinessIntelligenceFactory:
    """Test cases for business intelligence factory functions"""
    
    def test_get_business_intelligence_service(self, mock_db_session):
        """Test get_business_intelligence_service factory function"""
        service = get_business_intelligence_service(mock_db_session)
        
        assert service is not None
        assert isinstance(service, BusinessIntelligenceService)
        assert service.db == mock_db_session

if __name__ == "__main__":
    pytest.main([__file__]) 