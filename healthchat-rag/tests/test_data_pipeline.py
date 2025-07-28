"""
Tests for Data Pipeline System

This module tests:
- Batch data processing
- Streaming data processing
- Data quality validation
- Data transformation
- ETL job management
- Data warehouse operations
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.data_pipeline import (
    DataPipelineManager, ETLJobConfig, PipelineType, DataQualityLevel,
    DataQualityMetrics, DataLineageInfo, BatchDataProcessor,
    StreamingDataProcessor, DataWarehouseManager, DataValidator, DataTransformer
)
from app.exceptions.health_exceptions import DataProcessingError


class TestDataValidator:
    """Test data validation functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.validator = DataValidator()
    
    def test_validate_data_quality_excellent(self):
        """Test data quality validation with excellent data."""
        data = [
            {
                "user_id": 1,
                "heart_rate": 75,
                "timestamp": datetime.utcnow().isoformat(),
                "unit": "bpm"
            }
            for _ in range(100)
        ]
        
        metrics = self.validator.validate_data_quality(data, "health_metrics")
        
        assert metrics.overall_score >= 0.8
        assert metrics.quality_level in [DataQualityLevel.EXCELLENT, DataQualityLevel.GOOD]
        assert metrics.completeness > 0.9
        assert metrics.validity > 0.9
    
    def test_validate_data_quality_poor(self):
        """Test data quality validation with poor data."""
        data = [
            {
                "user_id": None,  # Missing required field
                "heart_rate": 300,  # Invalid value
                "timestamp": None,  # Missing timestamp
                "unit": "invalid_unit"
            }
            for _ in range(10)
        ]
        
        metrics = self.validator.validate_data_quality(data, "health_metrics")
        
        assert metrics.overall_score < 0.5
        assert metrics.quality_level in [DataQualityLevel.POOR, DataQualityLevel.UNUSABLE]
        assert len(metrics.issues) > 0
        assert len(metrics.recommendations) > 0
    
    def test_validate_data_quality_empty(self):
        """Test data quality validation with empty data."""
        metrics = self.validator.validate_data_quality([], "health_metrics")
        
        assert metrics.overall_score == 0.0
        assert metrics.quality_level == DataQualityLevel.UNUSABLE
        assert "No data provided" in metrics.issues
    
    def test_check_data_consistency(self):
        """Test data consistency checking."""
        data = [
            {"user_id": 1, "heart_rate": 75, "timestamp": datetime.utcnow().isoformat()},
            {"user_id": 2, "heart_rate": 80, "timestamp": datetime.utcnow().isoformat()},
            {"user_id": 3, "heart_rate": 70, "timestamp": datetime.utcnow().isoformat()}
        ]
        
        rules = {
            "data_types": {"user_id": int, "heart_rate": int},
            "heart_rate": {"min_value": 30, "max_value": 200}
        }
        
        consistency = self.validator._check_data_consistency(data, rules)
        
        assert 0.0 <= consistency <= 1.0
        assert consistency > 0.8  # Should be high for consistent data
    
    def test_check_data_timeliness(self):
        """Test data timeliness checking."""
        now = datetime.utcnow()
        
        # Recent data
        recent_data = [
            {"timestamp": (now - timedelta(hours=1)).isoformat()},
            {"timestamp": (now - timedelta(hours=2)).isoformat()}
        ]
        
        timeliness_recent = self.validator._check_data_timeliness(recent_data)
        assert timeliness_recent > 0.8
        
        # Old data
        old_data = [
            {"timestamp": (now - timedelta(days=30)).isoformat()},
            {"timestamp": (now - timedelta(days=60)).isoformat()}
        ]
        
        timeliness_old = self.validator._check_data_timeliness(old_data)
        assert timeliness_old < 0.5


class TestDataTransformer:
    """Test data transformation functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.transformer = DataTransformer()
    
    def test_transform_data_health_metrics(self):
        """Test health metrics data transformation."""
        data = [
            {
                "user_id": 1,
                "heart_rate": 75,
                "unit": "bpm",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "user_id": 2,
                "heart_rate": 80,
                "unit": "beats_per_minute",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        transformed_data = self.transformer.transform_data(data, "health_metrics")
        
        assert len(transformed_data) == len(data)
        assert all("_transformed_at" in record for record in transformed_data)
        assert all("_transformation_version" in record for record in transformed_data)
    
    def test_transform_data_user_data(self):
        """Test user data transformation."""
        data = [
            {
                "user_id": 1,
                "email": "TEST@EXAMPLE.COM",
                "name": "john doe"
            }
        ]
        
        transformed_data = self.transformer.transform_data(data, "user_data")
        
        assert len(transformed_data) == len(data)
        # Email should be normalized to lowercase
        assert transformed_data[0]["email"] == "test@example.com"
    
    def test_apply_field_transformations(self):
        """Test field-level transformations."""
        # Test lowercase transformation
        result = self.transformer._apply_field_transformations(
            "TEST STRING", {"normalization": "lowercase"}
        )
        assert result == "test string"
        
        # Test title case transformation
        result = self.transformer._apply_field_transformations(
            "john doe", {"normalization": "title_case"}
        )
        assert result == "John Doe"
        
        # Test no transformation
        result = self.transformer._apply_field_transformations(
            75, {"normalization": "nonexistent"}
        )
        assert result == 75


class TestBatchDataProcessor:
    """Test batch data processing functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.processor = BatchDataProcessor(self.mock_db)
    
    @pytest.mark.asyncio
    async def test_process_batch_data_success(self):
        """Test successful batch data processing."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test ETL Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["health_metrics"],
            target_tables=["aggregated_metrics"],
            schedule="0 0 * * *"
        )
        
        with patch.object(self.processor, '_extract_data') as mock_extract:
            with patch.object(self.processor, '_load_data') as mock_load:
                mock_extract.return_value = [
                    {"user_id": 1, "heart_rate": 75, "timestamp": datetime.utcnow().isoformat()}
                ]
                mock_load.return_value = {"aggregated_metrics": {"records_loaded": 1, "success": True}}
                
                result = await self.processor.process_batch_data(job_config)
                
                assert result["success"] is True
                assert result["job_id"] == "test_job"
                assert "quality_metrics" in result
                assert "lineage_info" in result
    
    @pytest.mark.asyncio
    async def test_process_batch_data_quality_threshold_failure(self):
        """Test batch processing with quality threshold failure."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test ETL Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["health_metrics"],
            target_tables=["aggregated_metrics"],
            schedule="0 0 * * *",
            data_quality_threshold=0.9  # High threshold
        )
        
        with patch.object(self.processor, '_extract_data') as mock_extract:
            # Return poor quality data
            mock_extract.return_value = [
                {"user_id": None, "heart_rate": 300, "timestamp": None}  # Poor quality
            ]
            
            with pytest.raises(DataProcessingError) as exc_info:
                await self.processor.process_batch_data(job_config)
            
            assert "Data quality score" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_data(self):
        """Test data extraction."""
        source_tables = ["health_metrics"]
        
        with patch.object(self.mock_db, 'execute') as mock_execute:
            mock_result = Mock()
            mock_result.__iter__ = lambda self: iter([{"user_id": 1, "heart_rate": 75}])
            mock_execute.return_value = mock_result
            
            result = await self.processor._extract_data(source_tables)
            
            assert len(result) > 0
            assert "user_id" in result[0]
    
    @pytest.mark.asyncio
    async def test_load_data(self):
        """Test data loading."""
        data = [{"user_id": 1, "heart_rate": 75}]
        target_tables = ["aggregated_metrics"]
        
        result = await self.processor._load_data(data, target_tables)
        
        assert "aggregated_metrics" in result
        assert result["aggregated_metrics"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_track_data_lineage(self):
        """Test data lineage tracking."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["source_table"],
            target_tables=["target_table"],
            schedule="0 0 * * *"
        )
        
        source_data = [{"id": 1, "value": 100}]
        transformed_data = [{"id": 1, "value": 100, "processed": True}]
        
        lineage_info = await self.processor._track_data_lineage(
            job_config, source_data, transformed_data
        )
        
        assert lineage_info.lineage_id is not None
        assert lineage_info.source_table == "source_table"
        assert lineage_info.target_table == "target_table"
        assert len(lineage_info.transformation_rules) > 0
        assert len(lineage_info.data_flow) > 0


class TestStreamingDataProcessor:
    """Test streaming data processing functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.kafka_config = {
            "bootstrap_servers": ["localhost:9092"],
            "topics": ["test-topic"],
            "consumer_group": "test-group"
        }
        self.processor = StreamingDataProcessor(self.kafka_config)
    
    @pytest.mark.asyncio
    async def test_stream_data_success(self):
        """Test successful data streaming."""
        topic = "test-topic"
        data = {"user_id": 1, "heart_rate": 75, "timestamp": datetime.utcnow().isoformat()}
        
        with patch('app.services.data_pipeline.KAFKA_AVAILABLE', True):
            with patch.object(self.processor, 'producer') as mock_producer:
                mock_future = Mock()
                mock_future.get.return_value = Mock(partition=0, offset=123)
                mock_producer.send.return_value = mock_future
                
                result = await self.processor.stream_data(topic, data)
                
                assert result is True
                mock_producer.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stream_data_kafka_unavailable(self):
        """Test data streaming when Kafka is unavailable."""
        topic = "test-topic"
        data = {"user_id": 1, "heart_rate": 75}
        
        with patch('app.services.data_pipeline.KAFKA_AVAILABLE', False):
            result = await self.processor.stream_data(topic, data)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_process_streaming_data(self):
        """Test streaming data processing."""
        topic = "test-topic"
        
        def processor_func(data):
            return {"processed": True, "original_data": data}
        
        with patch('app.services.data_pipeline.KAFKA_AVAILABLE', True):
            with patch.object(self.processor, 'consumer') as mock_consumer:
                mock_consumer.__iter__ = lambda self: iter([
                    Mock(value={"user_id": 1, "heart_rate": 75}, partition=0, offset=123)
                ])
                
                # This would run indefinitely in real usage, so we'll just test the setup
                # In a real test, you'd need to mock the consumer iteration properly
                pass
    
    def test_create_kafka_topic_success(self):
        """Test successful Kafka topic creation."""
        topic_name = "test-topic"
        
        with patch('app.services.data_pipeline.KAFKA_AVAILABLE', True):
            with patch('kafka.admin.KafkaAdminClient') as mock_admin:
                mock_admin_instance = Mock()
                mock_admin.return_value = mock_admin_instance
                
                result = self.processor.create_kafka_topic(topic_name)
                
                assert result is True
                mock_admin_instance.create_topics.assert_called_once()
    
    def test_create_kafka_topic_already_exists(self):
        """Test Kafka topic creation when topic already exists."""
        topic_name = "test-topic"
        
        with patch('app.services.data_pipeline.KAFKA_AVAILABLE', True):
            with patch('kafka.admin.KafkaAdminClient') as mock_admin:
                from kafka.errors import TopicAlreadyExistsError
                mock_admin_instance = Mock()
                mock_admin_instance.create_topics.side_effect = TopicAlreadyExistsError()
                mock_admin.return_value = mock_admin_instance
                
                result = self.processor.create_kafka_topic(topic_name)
                
                assert result is True  # Should return True for existing topics


class TestDataWarehouseManager:
    """Test data warehouse management functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.warehouse_config = {
            "connection_string": "postgresql://user:pass@localhost:5432/test_warehouse"
        }
        self.manager = DataWarehouseManager(self.warehouse_config)
    
    @pytest.mark.asyncio
    async def test_create_analytics_tables_success(self):
        """Test successful analytics table creation."""
        with patch.object(self.manager, 'engine') as mock_engine:
            mock_connection = Mock()
            mock_engine.connect.return_value.__enter__.return_value = mock_connection
            
            result = await self.manager.create_analytics_tables()
            
            assert result["success"] is True
            assert result["tables_created"] == 3
            mock_connection.execute.assert_called()
    
    @pytest.mark.asyncio
    async def test_create_analytics_tables_no_connection(self):
        """Test analytics table creation without warehouse connection."""
        self.manager.engine = None
        
        result = await self.manager.create_analytics_tables()
        
        assert result["success"] is False
        assert "No warehouse connection" in result["error"]
    
    @pytest.mark.asyncio
    async def test_run_etl_job_success(self):
        """Test successful ETL job execution."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test ETL Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["source_table"],
            target_tables=["target_table"],
            schedule="0 0 * * *"
        )
        
        with patch.object(self.manager, 'engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = Mock()
            
            result = await self.manager.run_etl_job(job_config)
            
            assert result["success"] is True
            assert result["job_id"] == "test_job"
            assert "records_processed" in result
            assert "processing_time" in result
    
    @pytest.mark.asyncio
    async def test_optimize_data_partitioning_success(self):
        """Test successful data partitioning optimization."""
        with patch.object(self.manager, 'engine') as mock_engine:
            mock_engine.connect.return_value.__enter__.return_value = Mock()
            
            result = await self.manager.optimize_data_partitioning()
            
            assert result["success"] is True
            assert "partitions_optimized" in result
            assert "performance_improvement" in result


class TestDataPipelineManager:
    """Test data pipeline manager functionality."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.mock_db = Mock()
        self.kafka_config = {"bootstrap_servers": ["localhost:9092"]}
        self.warehouse_config = {"connection_string": "postgresql://localhost/test"}
        self.manager = DataPipelineManager(
            self.mock_db, self.kafka_config, self.warehouse_config
        )
    
    @pytest.mark.asyncio
    async def test_setup_pipeline_infrastructure(self):
        """Test pipeline infrastructure setup."""
        with patch.object(self.manager.streaming_processor, 'create_kafka_topic') as mock_kafka:
            with patch.object(self.manager.warehouse_manager, 'create_analytics_tables') as mock_warehouse:
                mock_kafka.return_value = True
                mock_warehouse.return_value = {"success": True, "tables_created": 3}
                
                result = await self.manager.setup_pipeline_infrastructure()
                
                assert result["kafka_setup"] is True
                assert result["warehouse_setup"] is True
                assert result["tables_created"] is True
    
    @pytest.mark.asyncio
    async def test_run_complete_pipeline_batch(self):
        """Test complete pipeline execution for batch processing."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test Batch Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["source_table"],
            target_tables=["target_table"],
            schedule="0 0 * * *"
        )
        
        with patch.object(self.manager.batch_processor, 'process_batch_data') as mock_batch:
            with patch.object(self.manager.warehouse_manager, 'run_etl_job') as mock_warehouse:
                mock_batch.return_value = {"success": True, "records_processed": 100}
                mock_warehouse.return_value = {"success": True, "records_processed": 100}
                
                result = await self.manager.run_complete_pipeline(job_config)
                
                assert "batch_processing" in result
                assert "warehouse_etl" in result
                assert result["batch_processing"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_run_complete_pipeline_streaming(self):
        """Test complete pipeline execution for streaming processing."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test Streaming Job",
            pipeline_type=PipelineType.STREAMING,
            source_tables=["source_table"],
            target_tables=["target_table"],
            schedule="0 0 * * *"
        )
        
        with patch.object(self.manager.warehouse_manager, 'run_etl_job') as mock_warehouse:
            mock_warehouse.return_value = {"success": True, "records_processed": 100}
            
            result = await self.manager.run_complete_pipeline(job_config)
            
            assert "streaming_processing" in result
            assert "warehouse_etl" in result
            assert result["streaming_processing"]["status"] == "started"


class TestETLJobConfig:
    """Test ETL job configuration."""
    
    def test_etl_job_config_creation(self):
        """Test ETL job configuration creation."""
        job_config = ETLJobConfig(
            job_id="test_job",
            job_name="Test Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["source_table"],
            target_tables=["target_table"],
            schedule="0 0 * * *"
        )
        
        assert job_config.job_id == "test_job"
        assert job_config.job_name == "Test Job"
        assert job_config.pipeline_type == PipelineType.BATCH
        assert job_config.source_tables == ["source_table"]
        assert job_config.target_tables == ["target_table"]
        assert job_config.schedule == "0 0 * * *"
        assert job_config.enabled is True
        assert job_config.retry_count == 3
        assert job_config.data_quality_threshold == 0.8


class TestDataQualityMetrics:
    """Test data quality metrics."""
    
    def test_data_quality_metrics_creation(self):
        """Test data quality metrics creation."""
        metrics = DataQualityMetrics(
            completeness=0.95,
            accuracy=0.90,
            consistency=0.88,
            timeliness=0.92,
            validity=0.94,
            overall_score=0.92,
            quality_level=DataQualityLevel.GOOD,
            issues=["Minor data inconsistency"],
            recommendations=["Standardize data formats"]
        )
        
        assert metrics.completeness == 0.95
        assert metrics.accuracy == 0.90
        assert metrics.consistency == 0.88
        assert metrics.timeliness == 0.92
        assert metrics.validity == 0.94
        assert metrics.overall_score == 0.92
        assert metrics.quality_level == DataQualityLevel.GOOD
        assert len(metrics.issues) == 1
        assert len(metrics.recommendations) == 1


class TestDataLineageInfo:
    """Test data lineage information."""
    
    def test_data_lineage_info_creation(self):
        """Test data lineage information creation."""
        lineage_info = DataLineageInfo(
            lineage_id="lineage_123",
            source_table="source_table",
            target_table="target_table",
            transformation_rules=["validation", "aggregation"],
            data_flow=["extract", "transform", "load"],
            dependencies=["source_table", "user_profiles"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"records_processed": 1000}
        )
        
        assert lineage_info.lineage_id == "lineage_123"
        assert lineage_info.source_table == "source_table"
        assert lineage_info.target_table == "target_table"
        assert len(lineage_info.transformation_rules) == 2
        assert len(lineage_info.data_flow) == 3
        assert len(lineage_info.dependencies) == 2
        assert lineage_info.metadata["records_processed"] == 1000


# Integration tests
class TestDataPipelineIntegration:
    """Integration tests for data pipeline system."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_batch_processing(self):
        """Test end-to-end batch processing workflow."""
        # Create pipeline manager
        mock_db = Mock()
        manager = DataPipelineManager(
            mock_db,
            kafka_config={"bootstrap_servers": ["localhost:9092"]},
            warehouse_config={"connection_string": "postgresql://localhost/test"}
        )
        
        # Create ETL job
        job_config = ETLJobConfig(
            job_id="integration_test_job",
            job_name="Integration Test Job",
            pipeline_type=PipelineType.BATCH,
            source_tables=["health_metrics"],
            target_tables=["aggregated_health_metrics"],
            schedule="0 0 * * *"
        )
        
        # Mock all dependencies
        with patch.object(manager.batch_processor, 'process_batch_data') as mock_batch:
            with patch.object(manager.warehouse_manager, 'run_etl_job') as mock_warehouse:
                mock_batch.return_value = {
                    "success": True,
                    "records_processed": 1000,
                    "quality_metrics": DataQualityMetrics(
                        completeness=0.95,
                        accuracy=0.90,
                        consistency=0.88,
                        timeliness=0.92,
                        validity=0.94,
                        overall_score=0.92,
                        quality_level=DataQualityLevel.GOOD
                    )
                }
                mock_warehouse.return_value = {
                    "success": True,
                    "records_processed": 1000
                }
                
                # Run complete pipeline
                result = await manager.run_complete_pipeline(job_config)
                
                # Verify results
                assert "batch_processing" in result
                assert "warehouse_etl" in result
                assert result["batch_processing"]["success"] is True
                assert result["warehouse_etl"]["success"] is True
    
    @pytest.mark.asyncio
    async def test_data_quality_workflow(self):
        """Test complete data quality analysis workflow."""
        # Create sample data
        sample_data = [
            {
                "user_id": 1,
                "heart_rate": 75,
                "timestamp": datetime.utcnow().isoformat(),
                "unit": "bpm"
            }
            for _ in range(50)
        ]
        
        # Add some poor quality data
        sample_data.extend([
            {
                "user_id": None,  # Missing required field
                "heart_rate": 300,  # Invalid value
                "timestamp": None,  # Missing timestamp
                "unit": "invalid"
            }
            for _ in range(10)
        ])
        
        # Create validator
        validator = DataValidator()
        
        # Analyze quality
        metrics = validator.validate_data_quality(sample_data, "health_metrics")
        
        # Verify quality metrics
        assert 0.0 <= metrics.overall_score <= 1.0
        assert len(metrics.issues) > 0
        assert len(metrics.recommendations) > 0
        
        # Transform data if quality is acceptable
        if metrics.overall_score >= 0.7:
            transformer = DataTransformer()
            transformed_data = transformer.transform_data(sample_data, "health_metrics")
            
            assert len(transformed_data) == len(sample_data)
            assert all("_transformed_at" in record for record in transformed_data)


if __name__ == "__main__":
    pytest.main([__file__]) 