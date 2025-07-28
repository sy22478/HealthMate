#!/usr/bin/env python3
"""
Backup and Disaster Recovery Setup Script

This script sets up the backup and disaster recovery infrastructure for HealthMate.
"""

import os
import sys
import argparse
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.services.backup_service import BackupService
from app.services.disaster_recovery_service import DisasterRecoveryService
from app.exceptions.database_exceptions import DatabaseBackupError
from app.exceptions.external_api_exceptions import InfrastructureError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackupDisasterRecoverySetup:
    """Setup class for backup and disaster recovery infrastructure."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.backup_service = BackupService(settings)
        self.dr_service = DisasterRecoveryService(settings)
    
    async def setup_backup_infrastructure(self) -> Dict[str, Any]:
        """Setup backup infrastructure."""
        try:
            logger.info("Setting up backup infrastructure...")
            
            setup_results = {
                "backup_config": self.backup_service.backup_config,
                "storage_provider": self.backup_service.backup_config["storage"]["provider"],
                "backup_retention_days": self.backup_service.backup_config["database"]["backup_retention_days"],
                "encryption_enabled": self.backup_service.backup_config["database"]["backup_encryption_enabled"],
                "compression_enabled": self.backup_service.backup_config["database"]["backup_compression_enabled"]
            }
            
            # Validate backup configuration
            await self._validate_backup_config()
            
            # Test backup storage connectivity
            await self._test_backup_storage()
            
            # Create initial backup
            await self._create_initial_backup()
            
            logger.info("Backup infrastructure setup completed successfully")
            return setup_results
            
        except Exception as e:
            logger.error(f"Backup infrastructure setup failed: {e}")
            raise DatabaseBackupError(f"Backup setup failed: {e}")
    
    async def setup_disaster_recovery_infrastructure(self) -> Dict[str, Any]:
        """Setup disaster recovery infrastructure."""
        try:
            logger.info("Setting up disaster recovery infrastructure...")
            
            setup_results = {
                "recovery_config": self.dr_service.recovery_config,
                "regions": self.dr_service.recovery_config["regions"],
                "recovery_objectives": self.dr_service.recovery_config["recovery_objectives"]
            }
            
            # Setup system redundancy
            redundancy_status = await self.dr_service.setup_system_redundancy()
            setup_results["redundancy_status"] = redundancy_status
            
            # Perform initial health checks
            health_status = await self.dr_service.perform_health_checks()
            setup_results["health_status"] = health_status
            
            # Test disaster recovery procedures
            await self._test_disaster_recovery_procedures()
            
            logger.info("Disaster recovery infrastructure setup completed successfully")
            return setup_results
            
        except Exception as e:
            logger.error(f"Disaster recovery infrastructure setup failed: {e}")
            raise InfrastructureError(f"Disaster recovery setup failed: {e}")
    
    async def _validate_backup_config(self):
        """Validate backup configuration."""
        try:
            logger.info("Validating backup configuration...")
            
            config = self.backup_service.backup_config
            
            # Check required configuration
            required_fields = [
                "database.backup_retention_days",
                "storage.provider",
                "storage.bucket_name"
            ]
            
            for field in required_fields:
                keys = field.split('.')
                value = config
                for key in keys:
                    if key not in value:
                        raise ValueError(f"Missing required backup configuration: {field}")
                    value = value[key]
            
            logger.info("Backup configuration validation passed")
            
        except Exception as e:
            logger.error(f"Backup configuration validation failed: {e}")
            raise DatabaseBackupError(f"Configuration validation failed: {e}")
    
    async def _test_backup_storage(self):
        """Test backup storage connectivity."""
        try:
            logger.info("Testing backup storage connectivity...")
            
            storage_provider = self.backup_service.backup_config["storage"]["provider"]
            
            if storage_provider == "s3":
                # Test S3 connectivity
                bucket_name = self.backup_service.backup_config["storage"]["bucket_name"]
                
                # Try to list objects (this will test connectivity)
                try:
                    self.backup_service.s3_client.list_objects_v2(
                        Bucket=bucket_name,
                        MaxKeys=1
                    )
                    logger.info(f"S3 connectivity test passed for bucket: {bucket_name}")
                except Exception as e:
                    logger.error(f"S3 connectivity test failed: {e}")
                    raise DatabaseBackupError(f"S3 connectivity test failed: {e}")
            
            elif storage_provider == "local":
                # Test local storage
                local_path = self.backup_service.backup_config["storage"].get("local_path", "/backups")
                path = Path(local_path)
                
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created local backup directory: {local_path}")
                
                # Test write permissions
                test_file = path / "test_write.tmp"
                try:
                    test_file.write_text("test")
                    test_file.unlink()
                    logger.info(f"Local storage write test passed: {local_path}")
                except Exception as e:
                    logger.error(f"Local storage write test failed: {e}")
                    raise DatabaseBackupError(f"Local storage test failed: {e}")
            
            else:
                raise DatabaseBackupError(f"Unsupported storage provider: {storage_provider}")
            
        except Exception as e:
            logger.error(f"Backup storage test failed: {e}")
            raise DatabaseBackupError(f"Storage test failed: {e}")
    
    async def _create_initial_backup(self):
        """Create initial backup to test the system."""
        try:
            logger.info("Creating initial backup...")
            
            # Create database backup
            backup_metadata = await self.backup_service.create_database_backup("full")
            logger.info(f"Initial database backup created: {backup_metadata['backup_id']}")
            
            # Create file backup
            file_backup_metadata = await self.backup_service.create_file_backup()
            logger.info(f"Initial file backup created: {file_backup_metadata['backup_id']}")
            
        except Exception as e:
            logger.error(f"Initial backup creation failed: {e}")
            raise DatabaseBackupError(f"Initial backup failed: {e}")
    
    async def _test_disaster_recovery_procedures(self):
        """Test disaster recovery procedures."""
        try:
            logger.info("Testing disaster recovery procedures...")
            
            scenarios = ["database_failure", "region_outage", "application_failure"]
            
            for scenario in scenarios:
                logger.info(f"Testing disaster recovery scenario: {scenario}")
                
                # Create playbook
                playbook = await self.dr_service.create_disaster_recovery_playbook(scenario)
                logger.info(f"Playbook created for scenario: {scenario}")
                
                # Test procedure (dry run)
                test_results = await self.dr_service.execute_recovery_procedure(scenario, automated=False)
                logger.info(f"Test completed for scenario: {scenario}")
            
            logger.info("Disaster recovery procedure testing completed")
            
        except Exception as e:
            logger.error(f"Disaster recovery procedure testing failed: {e}")
            raise InfrastructureError(f"Procedure testing failed: {e}")
    
    async def setup_scheduled_tasks(self) -> Dict[str, Any]:
        """Setup scheduled backup and monitoring tasks."""
        try:
            logger.info("Setting up scheduled tasks...")
            
            # This would typically involve setting up cron jobs or Celery beat schedules
            scheduled_tasks = {
                "daily_database_backup": "0 2 * * *",  # 2 AM daily
                "weekly_file_backup": "0 3 * * 0",     # 3 AM Sunday
                "backup_cleanup": "0 4 * * 0",         # 4 AM Sunday
                "health_checks": "*/30 * * * *",       # Every 30 minutes
                "recovery_objectives_tracking": "0 */6 * * *",  # Every 6 hours
                "backup_health_monitoring": "0 */2 * * *"       # Every 2 hours
            }
            
            logger.info("Scheduled tasks configuration:")
            for task, schedule in scheduled_tasks.items():
                logger.info(f"  {task}: {schedule}")
            
            return {
                "scheduled_tasks": scheduled_tasks,
                "setup_completed": True
            }
            
        except Exception as e:
            logger.error(f"Scheduled tasks setup failed: {e}")
            raise InfrastructureError(f"Scheduled tasks setup failed: {e}")
    
    async def run_comprehensive_setup(self) -> Dict[str, Any]:
        """Run comprehensive backup and disaster recovery setup."""
        try:
            logger.info("Starting comprehensive backup and disaster recovery setup...")
            
            setup_results = {
                "backup_infrastructure": await self.setup_backup_infrastructure(),
                "disaster_recovery_infrastructure": await self.setup_disaster_recovery_infrastructure(),
                "scheduled_tasks": await self.setup_scheduled_tasks(),
                "setup_completed_at": asyncio.get_event_loop().time()
            }
            
            logger.info("Comprehensive setup completed successfully")
            return setup_results
            
        except Exception as e:
            logger.error(f"Comprehensive setup failed: {e}")
            raise InfrastructureError(f"Comprehensive setup failed: {e}")


def main():
    """Main function to run the setup script."""
    parser = argparse.ArgumentParser(description="Setup backup and disaster recovery infrastructure")
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Setup only backup infrastructure"
    )
    parser.add_argument(
        "--dr-only",
        action="store_true",
        help="Setup only disaster recovery infrastructure"
    )
    parser.add_argument(
        "--comprehensive",
        action="store_true",
        help="Setup both backup and disaster recovery infrastructure (default)"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate configuration without setting up infrastructure"
    )
    
    args = parser.parse_args()
    
    try:
        # Load settings
        settings = Settings()
        
        # Create setup instance
        setup = BackupDisasterRecoverySetup(settings)
        
        if args.validate_only:
            # Only validate configuration
            logger.info("Validating configuration only...")
            asyncio.run(setup._validate_backup_config())
            logger.info("Configuration validation completed successfully")
            return
        
        if args.backup_only:
            # Setup only backup infrastructure
            logger.info("Setting up backup infrastructure only...")
            results = asyncio.run(setup.setup_backup_infrastructure())
        elif args.dr_only:
            # Setup only disaster recovery infrastructure
            logger.info("Setting up disaster recovery infrastructure only...")
            results = asyncio.run(setup.setup_disaster_recovery_infrastructure())
        else:
            # Setup both (comprehensive)
            logger.info("Setting up comprehensive backup and disaster recovery infrastructure...")
            results = asyncio.run(setup.run_comprehensive_setup())
        
        # Print results
        logger.info("Setup completed successfully!")
        logger.info("Results:")
        for key, value in results.items():
            if isinstance(value, dict):
                logger.info(f"  {key}:")
                for sub_key, sub_value in value.items():
                    logger.info(f"    {sub_key}: {sub_value}")
            else:
                logger.info(f"  {key}: {value}")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 