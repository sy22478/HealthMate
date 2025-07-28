"""
Backup Service for HealthMate

This module provides comprehensive backup capabilities including:
- Database backup automation
- File and asset backup
- Backup encryption and secure storage
- Backup integrity verification
- Point-in-time recovery
- Cross-region backup replication
"""

import os
import gzip
import json
import hashlib
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import boto3
import psycopg2
from psycopg2.extras import RealDictCursor
import tarfile
import tempfile
import shutil
from cryptography.fernet import Fernet
from botocore.exceptions import ClientError, NoCredentialsError

from app.config import Settings
from app.utils.encryption_utils import EncryptionUtils
from app.exceptions.database_exceptions import DatabaseBackupError
from app.exceptions.external_api_exceptions import StorageServiceError

logger = logging.getLogger(__name__)


class BackupService:
    """Comprehensive backup service for HealthMate application."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.encryption_utils = EncryptionUtils(settings)
        self.backup_config = self._load_backup_config()
        
        # Initialize storage clients
        self.s3_client = None
        self._init_storage_clients()
    
    def _load_backup_config(self) -> Dict[str, Any]:
        """Load backup configuration from settings."""
        return {
            "database": {
                "backup_retention_days": int(os.getenv("BACKUP_RETENTION_DAYS", "30")),
                "backup_encryption_enabled": os.getenv("BACKUP_ENCRYPTION_ENABLED", "true").lower() == "true",
                "backup_compression_enabled": os.getenv("BACKUP_COMPRESSION_ENABLED", "true").lower() == "true",
                "point_in_time_recovery": os.getenv("POINT_IN_TIME_RECOVERY", "true").lower() == "true",
                "backup_schedule": os.getenv("BACKUP_SCHEDULE", "daily"),  # daily, weekly, monthly
                "backup_time": os.getenv("BACKUP_TIME", "02:00"),  # 24-hour format
            },
            "files": {
                "backup_paths": [
                    "data/embeddings",
                    "data/medical_knowledge",
                    "logs",
                    "uploads"
                ],
                "exclude_patterns": [
                    "*.tmp",
                    "*.log",
                    "__pycache__",
                    ".git"
                ],
                "max_file_size_mb": int(os.getenv("MAX_BACKUP_FILE_SIZE_MB", "100")),
            },
            "storage": {
                "provider": os.getenv("BACKUP_STORAGE_PROVIDER", "s3"),  # s3, local, gcs
                "bucket_name": os.getenv("BACKUP_BUCKET_NAME", "healthmate-backups"),
                "region": os.getenv("BACKUP_STORAGE_REGION", "us-east-1"),
                "cross_region_replication": os.getenv("BACKUP_CROSS_REGION_REPLICATION", "false").lower() == "true",
                "replication_regions": os.getenv("BACKUP_REPLICATION_REGIONS", "").split(","),
            },
            "verification": {
                "verify_backup_integrity": os.getenv("VERIFY_BACKUP_INTEGRITY", "true").lower() == "true",
                "test_restore_after_backup": os.getenv("TEST_RESTORE_AFTER_BACKUP", "false").lower() == "true",
            }
        }
    
    def _init_storage_clients(self):
        """Initialize storage service clients."""
        try:
            if self.backup_config["storage"]["provider"] == "s3":
                self.s3_client = boto3.client(
                    's3',
                    region_name=self.backup_config["storage"]["region"],
                    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
                )
                logger.info("S3 backup storage client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize storage clients: {e}")
            raise StorageServiceError(f"Storage client initialization failed: {e}")
    
    async def create_database_backup(self, backup_type: str = "full") -> Dict[str, Any]:
        """
        Create a database backup.
        
        Args:
            backup_type: Type of backup ("full", "incremental", "differential")
            
        Returns:
            Dict containing backup metadata
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_id = f"db_backup_{backup_type}_{timestamp}"
            
            logger.info(f"Starting {backup_type} database backup: {backup_id}")
            
            # Create backup directory
            backup_dir = Path(f"/tmp/backups/{backup_id}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create database dump
            dump_file = await self._create_database_dump(backup_dir, backup_type)
            
            # Compress backup if enabled
            if self.backup_config["database"]["backup_compression_enabled"]:
                dump_file = await self._compress_backup_file(dump_file)
            
            # Encrypt backup if enabled
            if self.backup_config["database"]["backup_encryption_enabled"]:
                dump_file = await self._encrypt_backup_file(dump_file)
            
            # Calculate checksum
            checksum = await self._calculate_file_checksum(dump_file)
            
            # Create backup metadata
            metadata = {
                "backup_id": backup_id,
                "backup_type": backup_type,
                "timestamp": timestamp,
                "created_at": datetime.utcnow().isoformat(),
                "file_path": str(dump_file),
                "file_size": dump_file.stat().st_size,
                "checksum": checksum,
                "compressed": self.backup_config["database"]["backup_compression_enabled"],
                "encrypted": self.backup_config["database"]["backup_encryption_enabled"],
                "database_version": await self._get_database_version(),
                "backup_format": "postgresql_dump"
            }
            
            # Save metadata
            metadata_file = backup_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload to storage
            await self._upload_backup_to_storage(backup_dir, backup_id)
            
            # Verify backup integrity
            if self.backup_config["verification"]["verify_backup_integrity"]:
                await self._verify_backup_integrity(backup_id, checksum)
            
            # Clean up local files
            shutil.rmtree(backup_dir)
            
            logger.info(f"Database backup completed successfully: {backup_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise DatabaseBackupError(f"Database backup failed: {e}")
    
    async def _create_database_dump(self, backup_dir: Path, backup_type: str) -> Path:
        """Create database dump using pg_dump."""
        try:
            # Parse database connection string
            db_url = self.settings.postgres_uri
            dump_file = backup_dir / f"database_dump_{backup_type}.sql"
            
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "--verbose",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                "--format=plain"
            ]
            
            # Add format-specific options
            if backup_type == "full":
                cmd.extend(["--schema-only", "--data-only"])
            elif backup_type == "incremental":
                # For incremental, we need to track changes
                cmd.extend(["--data-only"])
            
            # Add connection parameters
            if "://" in db_url:
                cmd.extend([db_url])
            else:
                # Parse connection string manually
                cmd.extend(["--host", "localhost", "--port", "5432", "--username", "postgres"])
            
            cmd.extend(["--file", str(dump_file)])
            
            # Execute pg_dump
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DatabaseBackupError(f"pg_dump failed: {stderr.decode()}")
            
            logger.info(f"Database dump created: {dump_file}")
            return dump_file
            
        except Exception as e:
            logger.error(f"Failed to create database dump: {e}")
            raise DatabaseBackupError(f"Database dump creation failed: {e}")
    
    async def _compress_backup_file(self, file_path: Path) -> Path:
        """Compress backup file using gzip."""
        try:
            compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original file
            file_path.unlink()
            
            logger.info(f"Backup file compressed: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Failed to compress backup file: {e}")
            raise DatabaseBackupError(f"Backup compression failed: {e}")
    
    async def _encrypt_backup_file(self, file_path: Path) -> Path:
        """Encrypt backup file."""
        try:
            encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
            
            # Generate encryption key
            encryption_key = Fernet.generate_key()
            cipher = Fernet(encryption_key)
            
            # Read and encrypt file
            with open(file_path, 'rb') as f:
                data = f.read()
            
            encrypted_data = cipher.encrypt(data)
            
            # Write encrypted file
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Save encryption key securely (in production, use KMS)
            key_file = file_path.parent / f"{file_path.stem}_key.txt"
            with open(key_file, 'wb') as f:
                f.write(encryption_key)
            
            # Remove original file
            file_path.unlink()
            
            logger.info(f"Backup file encrypted: {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            logger.error(f"Failed to encrypt backup file: {e}")
            raise DatabaseBackupError(f"Backup encryption failed: {e}")
    
    async def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of file."""
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            return sha256_hash.hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            raise DatabaseBackupError(f"Checksum calculation failed: {e}")
    
    async def _get_database_version(self) -> str:
        """Get PostgreSQL database version."""
        try:
            conn = psycopg2.connect(self.settings.postgres_uri)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            return version
        except Exception as e:
            logger.warning(f"Could not get database version: {e}")
            return "unknown"
    
    async def _upload_backup_to_storage(self, backup_dir: Path, backup_id: str):
        """Upload backup to storage service."""
        try:
            if self.backup_config["storage"]["provider"] == "s3":
                await self._upload_to_s3(backup_dir, backup_id)
            elif self.backup_config["storage"]["provider"] == "local":
                await self._copy_to_local_storage(backup_dir, backup_id)
            else:
                raise StorageServiceError(f"Unsupported storage provider: {self.backup_config['storage']['provider']}")
                
        except Exception as e:
            logger.error(f"Failed to upload backup to storage: {e}")
            raise StorageServiceError(f"Backup upload failed: {e}")
    
    async def _upload_to_s3(self, backup_dir: Path, backup_id: str):
        """Upload backup to S3."""
        try:
            bucket_name = self.backup_config["storage"]["bucket_name"]
            
            # Upload all files in backup directory
            for file_path in backup_dir.rglob("*"):
                if file_path.is_file():
                    # Create S3 key
                    relative_path = file_path.relative_to(backup_dir)
                    s3_key = f"backups/{backup_id}/{relative_path}"
                    
                    # Upload file
                    self.s3_client.upload_file(
                        str(file_path),
                        bucket_name,
                        s3_key,
                        ExtraArgs={
                            'ServerSideEncryption': 'AES256',
                            'Metadata': {
                                'backup_id': backup_id,
                                'uploaded_at': datetime.utcnow().isoformat()
                            }
                        }
                    )
                    
                    logger.info(f"Uploaded to S3: {s3_key}")
            
            # Enable cross-region replication if configured
            if self.backup_config["storage"]["cross_region_replication"]:
                await self._setup_cross_region_replication(backup_id)
                
        except Exception as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise StorageServiceError(f"S3 upload failed: {e}")
    
    async def _copy_to_local_storage(self, backup_dir: Path, backup_id: str):
        """Copy backup to local storage."""
        try:
            local_backup_path = Path(self.backup_config["storage"].get("local_path", "/backups"))
            destination = local_backup_path / backup_id
            
            # Copy entire backup directory
            shutil.copytree(backup_dir, destination)
            
            logger.info(f"Backup copied to local storage: {destination}")
            
        except Exception as e:
            logger.error(f"Failed to copy to local storage: {e}")
            raise StorageServiceError(f"Local storage copy failed: {e}")
    
    async def _setup_cross_region_replication(self, backup_id: str):
        """Setup cross-region replication for backup."""
        try:
            source_bucket = self.backup_config["storage"]["bucket_name"]
            source_region = self.backup_config["storage"]["region"]
            
            for target_region in self.backup_config["storage"]["replication_regions"]:
                if target_region.strip():
                    # Create replication configuration
                    replication_config = {
                        'Role': f'arn:aws:iam::account:role/s3-replication-role',
                        'Rules': [{
                            'ID': f'replication-{backup_id}',
                            'Status': 'Enabled',
                            'Priority': 1,
                            'Destination': {
                                'Bucket': f'arn:aws:s3:::{source_bucket}-{target_region}',
                                'StorageClass': 'STANDARD_IA'
                            }
                        }]
                    }
                    
                    # Apply replication configuration
                    self.s3_client.put_bucket_replication(
                        Bucket=source_bucket,
                        ReplicationConfiguration=replication_config
                    )
                    
                    logger.info(f"Cross-region replication configured for {target_region}")
                    
        except Exception as e:
            logger.warning(f"Failed to setup cross-region replication: {e}")
    
    async def _verify_backup_integrity(self, backup_id: str, expected_checksum: str):
        """Verify backup integrity by checking checksum."""
        try:
            # Download backup file for verification
            temp_dir = Path(tempfile.mkdtemp())
            
            if self.backup_config["storage"]["provider"] == "s3":
                bucket_name = self.backup_config["storage"]["bucket_name"]
                s3_key = f"backups/{backup_id}/database_dump_full.sql"
                
                # Download file
                local_file = temp_dir / "backup_file"
                self.s3_client.download_file(bucket_name, s3_key, str(local_file))
                
                # Calculate checksum
                actual_checksum = await self._calculate_file_checksum(local_file)
                
                # Verify checksum
                if actual_checksum != expected_checksum:
                    raise DatabaseBackupError("Backup integrity check failed: checksum mismatch")
                
                logger.info(f"Backup integrity verified: {backup_id}")
            
            # Clean up
            shutil.rmtree(temp_dir)
            
        except Exception as e:
            logger.error(f"Backup integrity verification failed: {e}")
            raise DatabaseBackupError(f"Backup integrity verification failed: {e}")
    
    async def create_file_backup(self) -> Dict[str, Any]:
        """
        Create backup of files and assets.
        
        Returns:
            Dict containing backup metadata
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_id = f"file_backup_{timestamp}"
            
            logger.info(f"Starting file backup: {backup_id}")
            
            # Create backup directory
            backup_dir = Path(f"/tmp/backups/{backup_id}")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Create file archive
            archive_file = await self._create_file_archive(backup_dir)
            
            # Compress archive if enabled
            if self.backup_config["database"]["backup_compression_enabled"]:
                archive_file = await self._compress_backup_file(archive_file)
            
            # Encrypt archive if enabled
            if self.backup_config["database"]["backup_encryption_enabled"]:
                archive_file = await self._encrypt_backup_file(archive_file)
            
            # Calculate checksum
            checksum = await self._calculate_file_checksum(archive_file)
            
            # Create backup metadata
            metadata = {
                "backup_id": backup_id,
                "backup_type": "file",
                "timestamp": timestamp,
                "created_at": datetime.utcnow().isoformat(),
                "file_path": str(archive_file),
                "file_size": archive_file.stat().st_size,
                "checksum": checksum,
                "compressed": self.backup_config["database"]["backup_compression_enabled"],
                "encrypted": self.backup_config["database"]["backup_encryption_enabled"],
                "backup_format": "tar"
            }
            
            # Save metadata
            metadata_file = backup_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload to storage
            await self._upload_backup_to_storage(backup_dir, backup_id)
            
            # Clean up local files
            shutil.rmtree(backup_dir)
            
            logger.info(f"File backup completed successfully: {backup_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"File backup failed: {e}")
            raise DatabaseBackupError(f"File backup failed: {e}")
    
    async def _create_file_archive(self, backup_dir: Path) -> Path:
        """Create tar archive of files to backup."""
        try:
            archive_file = backup_dir / "files_backup.tar"
            
            with tarfile.open(archive_file, 'w') as tar:
                for backup_path in self.backup_config["files"]["backup_paths"]:
                    path = Path(backup_path)
                    if path.exists():
                        # Add files to archive, excluding patterns
                        for file_path in path.rglob("*"):
                            if file_path.is_file():
                                # Check if file should be excluded
                                if not self._should_exclude_file(file_path):
                                    # Check file size limit
                                    if file_path.stat().st_size <= self.backup_config["files"]["max_file_size_mb"] * 1024 * 1024:
                                        tar.add(file_path, arcname=file_path.relative_to(Path.cwd()))
            
            logger.info(f"File archive created: {archive_file}")
            return archive_file
            
        except Exception as e:
            logger.error(f"Failed to create file archive: {e}")
            raise DatabaseBackupError(f"File archive creation failed: {e}")
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from backup."""
        for pattern in self.backup_config["files"]["exclude_patterns"]:
            if pattern.startswith("*."):
                # File extension pattern
                if file_path.suffix == pattern[1:]:
                    return True
            elif pattern in file_path.name or pattern in str(file_path):
                return True
        return False
    
    async def list_backups(self, backup_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available backups.
        
        Args:
            backup_type: Filter by backup type ("database", "file", None for all)
            
        Returns:
            List of backup metadata
        """
        try:
            backups = []
            
            if self.backup_config["storage"]["provider"] == "s3":
                bucket_name = self.backup_config["storage"]["bucket_name"]
                
                # List objects in backup bucket
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=bucket_name, Prefix="backups/")
                
                for page in pages:
                    for obj in page.get('Contents', []):
                        if obj['Key'].endswith('metadata.json'):
                            # Download and parse metadata
                            response = self.s3_client.get_object(Bucket=bucket_name, Key=obj['Key'])
                            metadata = json.loads(response['Body'].read().decode('utf-8'))
                            
                            if backup_type is None or metadata.get('backup_type') == backup_type:
                                backups.append(metadata)
            
            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            
            return backups
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            raise DatabaseBackupError(f"Backup listing failed: {e}")
    
    async def restore_backup(self, backup_id: str, restore_type: str = "full") -> Dict[str, Any]:
        """
        Restore from backup.
        
        Args:
            backup_id: ID of backup to restore from
            restore_type: Type of restore ("full", "partial")
            
        Returns:
            Dict containing restore status
        """
        try:
            logger.info(f"Starting backup restore: {backup_id}")
            
            # Get backup metadata
            backups = await self.list_backups()
            backup_metadata = next((b for b in backups if b['backup_id'] == backup_id), None)
            
            if not backup_metadata:
                raise DatabaseBackupError(f"Backup not found: {backup_id}")
            
            # Create restore directory
            restore_dir = Path(f"/tmp/restore/{backup_id}")
            restore_dir.mkdir(parents=True, exist_ok=True)
            
            # Download backup files
            await self._download_backup_from_storage(backup_id, restore_dir)
            
            # Restore based on backup type
            if backup_metadata['backup_type'] in ['full', 'incremental', 'differential']:
                await self._restore_database_backup(backup_id, restore_dir, restore_type)
            elif backup_metadata['backup_type'] == 'file':
                await self._restore_file_backup(backup_id, restore_dir)
            
            # Clean up
            shutil.rmtree(restore_dir)
            
            restore_status = {
                "backup_id": backup_id,
                "restore_type": restore_type,
                "restored_at": datetime.utcnow().isoformat(),
                "status": "completed"
            }
            
            logger.info(f"Backup restore completed: {backup_id}")
            return restore_status
            
        except Exception as e:
            logger.error(f"Backup restore failed: {e}")
            raise DatabaseBackupError(f"Backup restore failed: {e}")
    
    async def _download_backup_from_storage(self, backup_id: str, restore_dir: Path):
        """Download backup files from storage."""
        try:
            if self.backup_config["storage"]["provider"] == "s3":
                bucket_name = self.backup_config["storage"]["bucket_name"]
                
                # List and download all files for this backup
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(
                    Bucket=bucket_name,
                    Prefix=f"backups/{backup_id}/"
                )
                
                for page in pages:
                    for obj in page.get('Contents', []):
                        # Create local file path
                        relative_path = obj['Key'].replace(f"backups/{backup_id}/", "")
                        local_file = restore_dir / relative_path
                        local_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Download file
                        self.s3_client.download_file(bucket_name, obj['Key'], str(local_file))
                        
                        logger.info(f"Downloaded: {relative_path}")
            
        except Exception as e:
            logger.error(f"Failed to download backup from storage: {e}")
            raise StorageServiceError(f"Backup download failed: {e}")
    
    async def _restore_database_backup(self, backup_id: str, restore_dir: Path, restore_type: str):
        """Restore database from backup."""
        try:
            # Find database dump file
            dump_files = list(restore_dir.glob("database_dump_*.sql*"))
            if not dump_files:
                raise DatabaseBackupError("No database dump file found in backup")
            
            dump_file = dump_files[0]
            
            # Decrypt if necessary
            if dump_file.suffix == '.enc':
                dump_file = await self._decrypt_backup_file(dump_file)
            
            # Decompress if necessary
            if dump_file.suffix == '.gz':
                dump_file = await self._decompress_backup_file(dump_file)
            
            # Restore database
            await self._execute_database_restore(dump_file, restore_type)
            
        except Exception as e:
            logger.error(f"Failed to restore database backup: {e}")
            raise DatabaseBackupError(f"Database restore failed: {e}")
    
    async def _restore_file_backup(self, backup_id: str, restore_dir: Path):
        """Restore files from backup."""
        try:
            # Find file archive
            archive_files = list(restore_dir.glob("files_backup.tar*"))
            if not archive_files:
                raise DatabaseBackupError("No file archive found in backup")
            
            archive_file = archive_files[0]
            
            # Decrypt if necessary
            if archive_file.suffix == '.enc':
                archive_file = await self._decrypt_backup_file(archive_file)
            
            # Decompress if necessary
            if archive_file.suffix == '.gz':
                archive_file = await self._decompress_backup_file(archive_file)
            
            # Extract archive
            with tarfile.open(archive_file, 'r') as tar:
                tar.extractall(path=Path.cwd())
            
            logger.info("File backup restored successfully")
            
        except Exception as e:
            logger.error(f"Failed to restore file backup: {e}")
            raise DatabaseBackupError(f"File restore failed: {e}")
    
    async def _decrypt_backup_file(self, file_path: Path) -> Path:
        """Decrypt backup file."""
        try:
            decrypted_path = file_path.with_suffix('')
            
            # Find encryption key file
            key_file = file_path.parent / f"{file_path.stem.replace('.enc', '')}_key.txt"
            
            if not key_file.exists():
                raise DatabaseBackupError("Encryption key file not found")
            
            # Read encryption key
            with open(key_file, 'rb') as f:
                encryption_key = f.read()
            
            cipher = Fernet(encryption_key)
            
            # Read and decrypt file
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = cipher.decrypt(encrypted_data)
            
            # Write decrypted file
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)
            
            return decrypted_path
            
        except Exception as e:
            logger.error(f"Failed to decrypt backup file: {e}")
            raise DatabaseBackupError(f"Backup decryption failed: {e}")
    
    async def _decompress_backup_file(self, file_path: Path) -> Path:
        """Decompress backup file."""
        try:
            decompressed_path = file_path.with_suffix('')
            
            with gzip.open(file_path, 'rb') as f_in:
                with open(decompressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return decompressed_path
            
        except Exception as e:
            logger.error(f"Failed to decompress backup file: {e}")
            raise DatabaseBackupError(f"Backup decompression failed: {e}")
    
    async def _execute_database_restore(self, dump_file: Path, restore_type: str):
        """Execute database restore using psql."""
        try:
            # Build psql command
            cmd = ["psql", "--verbose"]
            
            # Add connection parameters
            db_url = self.settings.postgres_uri
            if "://" in db_url:
                cmd.extend([db_url])
            else:
                cmd.extend(["--host", "localhost", "--port", "5432", "--username", "postgres"])
            
            cmd.extend(["--file", str(dump_file)])
            
            # Execute psql
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise DatabaseBackupError(f"psql restore failed: {stderr.decode()}")
            
            logger.info("Database restore completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to execute database restore: {e}")
            raise DatabaseBackupError(f"Database restore execution failed: {e}")
    
    async def cleanup_old_backups(self) -> Dict[str, Any]:
        """
        Clean up old backups based on retention policy.
        
        Returns:
            Dict containing cleanup status
        """
        try:
            retention_days = self.backup_config["database"]["backup_retention_days"]
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            logger.info(f"Cleaning up backups older than {cutoff_date}")
            
            # Get all backups
            backups = await self.list_backups()
            
            deleted_backups = []
            for backup in backups:
                backup_date = datetime.fromisoformat(backup['created_at'].replace('Z', '+00:00'))
                if backup_date < cutoff_date:
                    await self._delete_backup(backup['backup_id'])
                    deleted_backups.append(backup['backup_id'])
            
            cleanup_status = {
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_backups": deleted_backups,
                "deleted_count": len(deleted_backups),
                "cleanup_completed_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Backup cleanup completed: {len(deleted_backups)} backups deleted")
            return cleanup_status
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            raise DatabaseBackupError(f"Backup cleanup failed: {e}")
    
    async def _delete_backup(self, backup_id: str):
        """Delete backup from storage."""
        try:
            if self.backup_config["storage"]["provider"] == "s3":
                bucket_name = self.backup_config["storage"]["bucket_name"]
                
                # List and delete all files for this backup
                paginator = self.s3_client.get_paginator('list_objects_v2')
                pages = paginator.paginate(
                    Bucket=bucket_name,
                    Prefix=f"backups/{backup_id}/"
                )
                
                objects_to_delete = []
                for page in pages:
                    for obj in page.get('Contents', []):
                        objects_to_delete.append({'Key': obj['Key']})
                
                if objects_to_delete:
                    self.s3_client.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': objects_to_delete}
                    )
                
                logger.info(f"Backup deleted: {backup_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            raise StorageServiceError(f"Backup deletion failed: {e}")
    
    async def get_backup_status(self) -> Dict[str, Any]:
        """
        Get comprehensive backup status and statistics.
        
        Returns:
            Dict containing backup status information
        """
        try:
            backups = await self.list_backups()
            
            # Calculate statistics
            total_backups = len(backups)
            database_backups = len([b for b in backups if b.get('backup_type') in ['full', 'incremental', 'differential']])
            file_backups = len([b for b in backups if b.get('backup_type') == 'file'])
            
            total_size = sum(b.get('file_size', 0) for b in backups)
            
            # Get latest backups
            latest_database = next((b for b in backups if b.get('backup_type') in ['full', 'incremental', 'differential']), None)
            latest_file = next((b for b in backups if b.get('backup_type') == 'file'), None)
            
            status = {
                "total_backups": total_backups,
                "database_backups": database_backups,
                "file_backups": file_backups,
                "total_size_bytes": total_size,
                "total_size_mb": total_size / (1024 * 1024),
                "latest_database_backup": latest_database,
                "latest_file_backup": latest_file,
                "backup_config": self.backup_config,
                "storage_provider": self.backup_config["storage"]["provider"],
                "retention_days": self.backup_config["database"]["backup_retention_days"],
                "status_checked_at": datetime.utcnow().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            raise DatabaseBackupError(f"Backup status retrieval failed: {e}") 