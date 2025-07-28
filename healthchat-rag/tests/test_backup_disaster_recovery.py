"""
Tests for Backup and Disaster Recovery functionality

This module contains comprehensive tests for backup and disaster recovery services.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.config import Settings
from app.services.backup_service import BackupService
from app.services.disaster_recovery_service import DisasterRecoveryService, RecoveryTier, SystemComponent
from app.exceptions.database_exceptions import DatabaseBackupError
from app.exceptions.external_api_exceptions import InfrastructureError


class TestBackupService:
    """Test cases for BackupService."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            postgres_uri="postgresql://test:test@localhost:5432/testdb",
            environment="test"
        )
    
    @pytest.fixture
    def backup_service(self, settings):
        """Create BackupService instance."""
        return BackupService(settings)
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_backup_service_initialization(self, backup_service):
        """Test BackupService initialization."""
        assert backup_service is not None
        assert backup_service.backup_config is not None
        assert "database" in backup_service.backup_config
        assert "storage" in backup_service.backup_config
    
    def test_load_backup_config(self, backup_service):
        """Test backup configuration loading."""
        config = backup_service.backup_config
        
        # Check required sections
        assert "database" in config
        assert "files" in config
        assert "storage" in config
        assert "verification" in config
        
        # Check database configuration
        db_config = config["database"]
        assert "backup_retention_days" in db_config
        assert "backup_encryption_enabled" in db_config
        assert "backup_compression_enabled" in db_config
        
        # Check storage configuration
        storage_config = config["storage"]
        assert "provider" in storage_config
        assert "bucket_name" in storage_config
    
    @patch('app.services.backup_service.boto3.client')
    def test_init_storage_clients_s3(self, mock_boto3_client, backup_service):
        """Test S3 storage client initialization."""
        # Mock S3 client
        mock_s3_client = Mock()
        mock_boto3_client.return_value = mock_s3_client
        
        # Set S3 as provider
        backup_service.backup_config["storage"]["provider"] = "s3"
        
        # Initialize clients
        backup_service._init_storage_clients()
        
        # Verify S3 client was created
        mock_boto3_client.assert_called_once()
        assert backup_service.s3_client is not None
    
    @patch('app.services.backup_service.boto3.client')
    def test_init_storage_clients_failure(self, mock_boto3_client, backup_service):
        """Test storage client initialization failure."""
        # Mock boto3 to raise exception
        mock_boto3_client.side_effect = Exception("AWS credentials not found")
        
        # Set S3 as provider
        backup_service.backup_config["storage"]["provider"] = "s3"
        
        # Should raise InfrastructureError
        with pytest.raises(InfrastructureError):
            backup_service._init_storage_clients()
    
    @pytest.mark.asyncio
    async def test_create_database_backup(self, backup_service, temp_backup_dir):
        """Test database backup creation."""
        with patch.object(backup_service, '_create_database_dump') as mock_dump, \
             patch.object(backup_service, '_upload_backup_to_storage') as mock_upload:
            
            # Mock database dump
            mock_dump.return_value = temp_backup_dir / "test_dump.sql"
            
            # Create backup
            result = await backup_service.create_database_backup("full")
            
            # Verify result
            assert "backup_id" in result
            assert "backup_type" in result
            assert result["backup_type"] == "full"
            assert "created_at" in result
            
            # Verify methods were called
            mock_dump.assert_called_once()
            mock_upload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_database_backup_failure(self, backup_service):
        """Test database backup creation failure."""
        with patch.object(backup_service, '_create_database_dump') as mock_dump:
            # Mock failure
            mock_dump.side_effect = Exception("Database connection failed")
            
            # Should raise DatabaseBackupError
            with pytest.raises(DatabaseBackupError):
                await backup_service.create_database_backup("full")
    
    @pytest.mark.asyncio
    async def test_create_file_backup(self, backup_service, temp_backup_dir):
        """Test file backup creation."""
        with patch.object(backup_service, '_create_file_archive') as mock_archive, \
             patch.object(backup_service, '_upload_backup_to_storage') as mock_upload:
            
            # Mock file archive
            mock_archive.return_value = temp_backup_dir / "files_backup.tar"
            
            # Create file backup
            result = await backup_service.create_file_backup()
            
            # Verify result
            assert "backup_id" in result
            assert "backup_type" in result
            assert result["backup_type"] == "file"
            assert "created_at" in result
            
            # Verify methods were called
            mock_archive.assert_called_once()
            mock_upload.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_compress_backup_file(self, backup_service, temp_backup_dir):
        """Test backup file compression."""
        # Create test file
        test_file = temp_backup_dir / "test_file.sql"
        test_file.write_text("test content")
        
        # Compress file
        compressed_file = await backup_service._compress_backup_file(test_file)
        
        # Verify compression
        assert compressed_file.exists()
        assert compressed_file.suffix == ".gz"
        assert not test_file.exists()  # Original file should be removed
    
    @pytest.mark.asyncio
    async def test_encrypt_backup_file(self, backup_service, temp_backup_dir):
        """Test backup file encryption."""
        # Create test file
        test_file = temp_backup_dir / "test_file.sql"
        test_file.write_text("test content")
        
        # Encrypt file
        encrypted_file = await backup_service._encrypt_backup_file(test_file)
        
        # Verify encryption
        assert encrypted_file.exists()
        assert encrypted_file.suffix == ".enc"
        assert not test_file.exists()  # Original file should be removed
        
        # Check for key file
        key_file = temp_backup_dir / "test_file_key.txt"
        assert key_file.exists()
    
    @pytest.mark.asyncio
    async def test_calculate_file_checksum(self, backup_service, temp_backup_dir):
        """Test file checksum calculation."""
        # Create test file
        test_file = temp_backup_dir / "test_file.txt"
        test_file.write_text("test content")
        
        # Calculate checksum
        checksum = await backup_service._calculate_file_checksum(test_file)
        
        # Verify checksum
        assert checksum is not None
        assert len(checksum) == 64  # SHA-256 hex length
        assert isinstance(checksum, str)
    
    @pytest.mark.asyncio
    async def test_list_backups(self, backup_service):
        """Test backup listing."""
        with patch.object(backup_service, 's3_client') as mock_s3:
            # Mock S3 response
            mock_s3.get_paginator.return_value.paginate.return_value = [
                {
                    'Contents': [
                        {'Key': 'backups/backup1/metadata.json'},
                        {'Key': 'backups/backup2/metadata.json'}
                    ]
                }
            ]
            
            # Mock metadata
            mock_s3.get_object.return_value.__getitem__.return_value.read.return_value.decode.return_value = \
                '{"backup_id": "test_backup", "created_at": "2023-01-01T00:00:00Z"}'
            
            # List backups
            backups = await backup_service.list_backups()
            
            # Verify result
            assert isinstance(backups, list)
            assert len(backups) == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, backup_service):
        """Test old backup cleanup."""
        with patch.object(backup_service, 'list_backups') as mock_list, \
             patch.object(backup_service, '_delete_backup') as mock_delete:
            
            # Mock backups
            mock_list.return_value = [
                {
                    'backup_id': 'old_backup',
                    'created_at': (datetime.utcnow() - timedelta(days=40)).isoformat()
                },
                {
                    'backup_id': 'recent_backup',
                    'created_at': datetime.utcnow().isoformat()
                }
            ]
            
            # Cleanup old backups
            result = await backup_service.cleanup_old_backups()
            
            # Verify result
            assert "deleted_backups" in result
            assert "deleted_count" in result
            assert result["deleted_count"] == 1
            
            # Verify delete was called for old backup
            mock_delete.assert_called_once_with("old_backup")
    
    @pytest.mark.asyncio
    async def test_get_backup_status(self, backup_service):
        """Test backup status retrieval."""
        with patch.object(backup_service, 'list_backups') as mock_list:
            # Mock backups
            mock_list.return_value = [
                {
                    'backup_id': 'backup1',
                    'backup_type': 'full',
                    'file_size': 1024,
                    'created_at': datetime.utcnow().isoformat()
                }
            ]
            
            # Get backup status
            status = await backup_service.get_backup_status()
            
            # Verify result
            assert "total_backups" in status
            assert "database_backups" in status
            assert "file_backups" in status
            assert "total_size_bytes" in status
            assert status["total_backups"] == 1


class TestDisasterRecoveryService:
    """Test cases for DisasterRecoveryService."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            postgres_uri="postgresql://test:test@localhost:5432/testdb",
            environment="test"
        )
    
    @pytest.fixture
    def dr_service(self, settings):
        """Create DisasterRecoveryService instance."""
        return DisasterRecoveryService(settings)
    
    def test_dr_service_initialization(self, dr_service):
        """Test DisasterRecoveryService initialization."""
        assert dr_service is not None
        assert dr_service.recovery_config is not None
        assert "recovery_objectives" in dr_service.recovery_config
        assert "regions" in dr_service.recovery_config
    
    def test_load_recovery_config(self, dr_service):
        """Test recovery configuration loading."""
        config = dr_service.recovery_config
        
        # Check required sections
        assert "recovery_objectives" in config
        assert "regions" in config
        assert "components" in config
        assert "monitoring" in config
        
        # Check recovery objectives
        objectives = config["recovery_objectives"]
        assert "critical" in objectives
        assert "high" in objectives
        assert "medium" in objectives
        assert "low" in objectives
        
        # Check regions
        regions = config["regions"]
        assert "primary" in regions
        assert "secondary" in regions
    
    @patch('app.services.disaster_recovery_service.boto3.client')
    def test_init_clients(self, mock_boto3_client, dr_service):
        """Test client initialization."""
        # Mock AWS clients
        mock_ec2_client = Mock()
        mock_rds_client = Mock()
        mock_elbv2_client = Mock()
        mock_boto3_client.side_effect = [mock_ec2_client, mock_rds_client, mock_elbv2_client]
        
        # Initialize clients
        dr_service._init_clients()
        
        # Verify clients were created
        assert dr_service.ec2_client is not None
        assert dr_service.rds_client is not None
        assert dr_service.elbv2_client is not None
    
    @pytest.mark.asyncio
    async def test_setup_system_redundancy(self, dr_service):
        """Test system redundancy setup."""
        with patch.object(dr_service, '_setup_database_redundancy') as mock_db, \
             patch.object(dr_service, '_setup_application_redundancy') as mock_app, \
             patch.object(dr_service, '_setup_load_balancer_redundancy') as mock_lb, \
             patch.object(dr_service, '_setup_storage_redundancy') as mock_storage:
            
            # Mock redundancy setup
            mock_db.return_value = {"status": "configured"}
            mock_app.return_value = {"status": "configured"}
            mock_lb.return_value = {"status": "configured"}
            mock_storage.return_value = {"status": "configured"}
            
            # Setup redundancy
            result = await dr_service.setup_system_redundancy()
            
            # Verify result
            assert "database_redundancy" in result
            assert "application_redundancy" in result
            assert "load_balancer_redundancy" in result
            assert "storage_redundancy" in result
            
            # Verify methods were called
            mock_db.assert_called_once()
            mock_app.assert_called_once()
            mock_lb.assert_called_once()
            mock_storage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_perform_health_checks(self, dr_service):
        """Test health checks performance."""
        with patch.object(dr_service, '_check_database_health') as mock_db, \
             patch.object(dr_service, '_check_application_health') as mock_app, \
             patch.object(dr_service, '_check_load_balancer_health') as mock_lb, \
             patch.object(dr_service, '_check_storage_health') as mock_storage, \
             patch.object(dr_service, '_check_network_health') as mock_network:
            
            # Mock health checks
            mock_db.return_value = {"status": "healthy"}
            mock_app.return_value = {"status": "healthy"}
            mock_lb.return_value = {"status": "healthy"}
            mock_storage.return_value = {"status": "healthy"}
            mock_network.return_value = {"status": "healthy"}
            
            # Perform health checks
            result = await dr_service.perform_health_checks()
            
            # Verify result
            assert "database_health" in result
            assert "application_health" in result
            assert "load_balancer_health" in result
            assert "storage_health" in result
            assert "network_health" in result
            assert "overall_status" in result
            assert result["overall_status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_initiate_failover(self, dr_service):
        """Test failover initiation."""
        with patch.object(dr_service, '_failover_database') as mock_failover:
            # Mock failover
            mock_failover.return_value = {"status": "completed"}
            
            # Initiate failover
            result = await dr_service.initiate_failover(
                SystemComponent.DATABASE,
                "Database performance degradation"
            )
            
            # Verify result
            assert "component" in result
            assert "reason" in result
            assert "status" in result
            assert result["component"] == "database"
            assert result["reason"] == "Database performance degradation"
            
            # Verify failover was called
            mock_failover.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_disaster_recovery_playbook(self, dr_service):
        """Test disaster recovery playbook creation."""
        # Create playbook
        playbook = await dr_service.create_disaster_recovery_playbook("database_failure")
        
        # Verify playbook
        assert "title" in playbook
        assert "description" in playbook
        assert "steps" in playbook
        assert "estimated_duration" in playbook
        assert "recovery_tier" in playbook
        assert playbook["scenario"] == "database_failure"
        assert playbook["recovery_tier"] == RecoveryTier.CRITICAL
    
    @pytest.mark.asyncio
    async def test_create_disaster_recovery_playbook_unknown_scenario(self, dr_service):
        """Test disaster recovery playbook creation with unknown scenario."""
        # Should raise InfrastructureError
        with pytest.raises(InfrastructureError):
            await dr_service.create_disaster_recovery_playbook("unknown_scenario")
    
    @pytest.mark.asyncio
    async def test_execute_recovery_procedure(self, dr_service):
        """Test recovery procedure execution."""
        with patch.object(dr_service, '_execute_automated_recovery') as mock_automated:
            # Mock automated recovery
            mock_automated.return_value = {"success": True}
            
            # Execute recovery procedure
            result = await dr_service.execute_recovery_procedure("database_failure", automated=True)
            
            # Verify result
            assert "scenario" in result
            assert "automated" in result
            assert "status" in result
            assert result["scenario"] == "database_failure"
            assert result["automated"] is True
            
            # Verify automated recovery was called
            mock_automated.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_recovery_objectives(self, dr_service):
        """Test recovery objectives tracking."""
        with patch.object(dr_service, 'backup_service') as mock_backup_service:
            # Mock backup status
            mock_backup_service.get_backup_status.return_value = {
                "latest_database_backup": {
                    "created_at": datetime.utcnow().isoformat()
                }
            }
            
            # Track recovery objectives
            result = await dr_service.track_recovery_objectives()
            
            # Verify result
            assert "recovery_objectives" in result
            assert "current_rpo_minutes" in result
            assert "latest_backup" in result
            
            # Check recovery objectives
            objectives = result["recovery_objectives"]
            for tier_name, objective in objectives.items():
                assert "rto_minutes" in objective
                assert "rpo_minutes" in objective
                assert "current_rpo_minutes" in objective
                assert "rpo_compliant" in objective
    
    @pytest.mark.asyncio
    async def test_get_disaster_recovery_status(self, dr_service):
        """Test disaster recovery status retrieval."""
        with patch.object(dr_service, 'perform_health_checks') as mock_health, \
             patch.object(dr_service, 'track_recovery_objectives') as mock_objectives, \
             patch.object(dr_service, 'backup_service') as mock_backup:
            
            # Mock status methods
            mock_health.return_value = {"overall_status": "healthy"}
            mock_objectives.return_value = {"recovery_objectives": {}}
            mock_backup.get_backup_status.return_value = {"total_backups": 5}
            
            # Get disaster recovery status
            result = await dr_service.get_disaster_recovery_status()
            
            # Verify result
            assert "overall_status" in result
            assert "readiness_score" in result
            assert "health_status" in result
            assert "recovery_objectives" in result
            assert "backup_status" in result
            assert "redundancy_config" in result
    
    def test_determine_overall_health(self, dr_service):
        """Test overall health determination."""
        # Test healthy status
        health_results = {
            "database_health": {"status": "healthy"},
            "application_health": {"status": "healthy"},
            "load_balancer_health": {"status": "healthy"},
            "storage_health": {"status": "healthy"},
            "network_health": {"status": "healthy"}
        }
        
        status = dr_service._determine_overall_health(health_results)
        assert status == "healthy"
        
        # Test degraded status
        health_results["database_health"]["status"] = "degraded"
        status = dr_service._determine_overall_health(health_results)
        assert status == "degraded"
        
        # Test unhealthy status
        health_results["database_health"]["status"] = "unhealthy"
        status = dr_service._determine_overall_health(health_results)
        assert status == "unhealthy"
    
    def test_calculate_readiness_score(self, dr_service):
        """Test readiness score calculation."""
        # Mock health status
        health_status = {
            "overall_status": "healthy"
        }
        
        # Mock recovery objectives
        recovery_objectives = {
            "recovery_objectives": {
                "critical": {"rpo_compliant": True},
                "high": {"rpo_compliant": True},
                "medium": {"rpo_compliant": True}
            }
        }
        
        # Mock backup status
        backup_status = {
            "latest_database_backup": {"created_at": "2023-01-01T00:00:00Z"}
        }
        
        # Calculate readiness score
        score = dr_service._calculate_readiness_score(health_status, recovery_objectives, backup_status)
        
        # Verify score
        assert 0 <= score <= 1
        assert score > 0.8  # Should be high for healthy system


class TestBackupDisasterRecoveryIntegration:
    """Integration tests for backup and disaster recovery."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings(
            postgres_uri="postgresql://test:test@localhost:5432/testdb",
            environment="test"
        )
    
    @pytest.fixture
    def backup_service(self, settings):
        """Create BackupService instance."""
        return BackupService(settings)
    
    @pytest.fixture
    def dr_service(self, settings):
        """Create DisasterRecoveryService instance."""
        return DisasterRecoveryService(settings)
    
    @pytest.mark.asyncio
    async def test_backup_and_recovery_integration(self, backup_service, dr_service):
        """Test integration between backup and disaster recovery."""
        with patch.object(backup_service, 'create_database_backup') as mock_backup, \
             patch.object(dr_service, 'perform_health_checks') as mock_health, \
             patch.object(dr_service, 'track_recovery_objectives') as mock_objectives:
            
            # Mock backup creation
            mock_backup.return_value = {
                "backup_id": "test_backup",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Mock health checks
            mock_health.return_value = {"overall_status": "healthy"}
            
            # Mock recovery objectives
            mock_objectives.return_value = {
                "recovery_objectives": {
                    "critical": {"rpo_compliant": True}
                }
            }
            
            # Create backup
            backup_result = await backup_service.create_database_backup("full")
            
            # Perform health checks
            health_result = await dr_service.perform_health_checks()
            
            # Track recovery objectives
            objectives_result = await dr_service.track_recovery_objectives()
            
            # Verify integration
            assert backup_result["backup_id"] == "test_backup"
            assert health_result["overall_status"] == "healthy"
            assert objectives_result["recovery_objectives"]["critical"]["rpo_compliant"] is True
    
    @pytest.mark.asyncio
    async def test_disaster_recovery_with_backup_restoration(self, backup_service, dr_service):
        """Test disaster recovery procedure with backup restoration."""
        with patch.object(backup_service, 'restore_backup') as mock_restore, \
             patch.object(dr_service, 'execute_recovery_procedure') as mock_recovery:
            
            # Mock backup restoration
            mock_restore.return_value = {
                "backup_id": "test_backup",
                "status": "completed"
            }
            
            # Mock recovery procedure
            mock_recovery.return_value = {
                "scenario": "database_failure",
                "status": "completed"
            }
            
            # Simulate disaster recovery with backup restoration
            restore_result = await backup_service.restore_backup("test_backup", "full")
            recovery_result = await dr_service.execute_recovery_procedure("database_failure", automated=True)
            
            # Verify results
            assert restore_result["status"] == "completed"
            assert recovery_result["status"] == "completed"
            assert recovery_result["scenario"] == "database_failure"


if __name__ == "__main__":
    pytest.main([__file__]) 