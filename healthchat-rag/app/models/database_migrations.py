"""
Database Migration System for HealthMate

This module provides a comprehensive migration system for database schema changes,
index optimizations, and constraint management.
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text, inspect, Index, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import json
import hashlib

logger = logging.getLogger(__name__)

class DatabaseMigration:
    """Database migration management class."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.inspector = inspect(self.db.bind)
    
    def create_migration_table(self):
        """Create the migration tracking table."""
        try:
            create_table_query = text("""
                CREATE TABLE IF NOT EXISTS database_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) NOT NULL UNIQUE,
                    migration_hash VARCHAR(64) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER,
                    status VARCHAR(20) DEFAULT 'success',
                    error_message TEXT,
                    rollback_sql TEXT,
                    metadata JSONB
                )
            """)
            
            self.db.execute(create_table_query)
            self.db.commit()
            
            logger.info("Migration tracking table created successfully")
            
        except SQLAlchemyError as e:
            logger.error(f"Error creating migration table: {e}")
            self.db.rollback()
    
    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration names."""
        try:
            query = text("SELECT migration_name FROM database_migrations ORDER BY applied_at")
            result = self.db.execute(query)
            return [row.migration_name for row in result]
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting applied migrations: {e}")
            return []
    
    def is_migration_applied(self, migration_name: str) -> bool:
        """Check if a migration has been applied."""
        try:
            query = text("SELECT COUNT(*) FROM database_migrations WHERE migration_name = :name")
            result = self.db.execute(query, {'name': migration_name})
            count = result.scalar()
            return count > 0
            
        except SQLAlchemyError as e:
            logger.error(f"Error checking migration status: {e}")
            return False
    
    def apply_migration(
        self, 
        migration_name: str, 
        sql_statements: List[str], 
        rollback_sql: List[str] = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """
        Apply a database migration.
        
        Args:
            migration_name: Name of the migration
            sql_statements: List of SQL statements to execute
            rollback_sql: List of SQL statements for rollback
            metadata: Additional metadata for the migration
            
        Returns:
            Migration result
        """
        start_time = datetime.utcnow()
        
        try:
            # Check if migration already applied
            if self.is_migration_applied(migration_name):
                return {
                    'success': False,
                    'message': f'Migration {migration_name} already applied',
                    'migration_name': migration_name
                }
            
            # Create migration hash
            migration_content = '\n'.join(sql_statements)
            migration_hash = hashlib.sha256(migration_content.encode()).hexdigest()
            
            # Execute migration statements
            for i, sql in enumerate(sql_statements):
                logger.info(f"Executing migration {migration_name} statement {i+1}/{len(sql_statements)}")
                self.db.execute(text(sql))
            
            self.db.commit()
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Record migration
            insert_query = text("""
                INSERT INTO database_migrations 
                (migration_name, migration_hash, execution_time_ms, rollback_sql, metadata)
                VALUES (:name, :hash, :exec_time, :rollback, :metadata)
            """)
            
            self.db.execute(insert_query, {
                'name': migration_name,
                'hash': migration_hash,
                'exec_time': int(execution_time),
                'rollback': json.dumps(rollback_sql) if rollback_sql else None,
                'metadata': json.dumps(metadata) if metadata else None
            })
            
            self.db.commit()
            
            logger.info(f"Migration {migration_name} applied successfully in {execution_time:.2f}ms")
            
            return {
                'success': True,
                'message': f'Migration {migration_name} applied successfully',
                'migration_name': migration_name,
                'execution_time_ms': int(execution_time)
            }
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error applying migration {migration_name}: {e}")
            
            # Record failed migration
            try:
                insert_query = text("""
                    INSERT INTO database_migrations 
                    (migration_name, migration_hash, execution_time_ms, status, error_message)
                    VALUES (:name, :hash, :exec_time, 'failed', :error)
                """)
                
                execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                migration_content = '\n'.join(sql_statements)
                migration_hash = hashlib.sha256(migration_content.encode()).hexdigest()
                
                self.db.execute(insert_query, {
                    'name': migration_name,
                    'hash': migration_hash,
                    'exec_time': int(execution_time),
                    'error': str(e)
                })
                
                self.db.commit()
                
            except SQLAlchemyError as record_error:
                logger.error(f"Error recording failed migration: {record_error}")
            
            return {
                'success': False,
                'message': f'Migration {migration_name} failed: {str(e)}',
                'migration_name': migration_name,
                'error': str(e)
            }
    
    def rollback_migration(self, migration_name: str) -> Dict[str, Any]:
        """
        Rollback a database migration.
        
        Args:
            migration_name: Name of the migration to rollback
            
        Returns:
            Rollback result
        """
        try:
            # Get migration details
            query = text("""
                SELECT rollback_sql, status FROM database_migrations 
                WHERE migration_name = :name
            """)
            
            result = self.db.execute(query, {'name': migration_name})
            migration = result.fetchone()
            
            if not migration:
                return {
                    'success': False,
                    'message': f'Migration {migration_name} not found'
                }
            
            if migration.status != 'success':
                return {
                    'success': False,
                    'message': f'Cannot rollback migration {migration_name} with status {migration.status}'
                }
            
            rollback_sql = json.loads(migration.rollback_sql) if migration.rollback_sql else []
            
            if not rollback_sql:
                return {
                    'success': False,
                    'message': f'No rollback SQL available for migration {migration_name}'
                }
            
            # Execute rollback statements
            for i, sql in enumerate(rollback_sql):
                logger.info(f"Executing rollback for {migration_name} statement {i+1}/{len(rollback_sql)}")
                self.db.execute(text(sql))
            
            # Remove migration record
            delete_query = text("DELETE FROM database_migrations WHERE migration_name = :name")
            self.db.execute(delete_query, {'name': migration_name})
            
            self.db.commit()
            
            logger.info(f"Migration {migration_name} rolled back successfully")
            
            return {
                'success': True,
                'message': f'Migration {migration_name} rolled back successfully',
                'migration_name': migration_name
            }
            
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Error rolling back migration {migration_name}: {e}")
            
            return {
                'success': False,
                'message': f'Error rolling back migration {migration_name}: {str(e)}',
                'error': str(e)
            }

class IndexMigration:
    """Index-specific migration utilities."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.inspector = inspect(self.db.bind)
    
    def create_index_migration(self, table_name: str, columns: List[str], index_name: str = None) -> Dict[str, Any]:
        """
        Create a migration for adding an index.
        
        Args:
            table_name: Name of the table
            columns: List of columns for the index
            index_name: Optional custom index name
            
        Returns:
            Migration configuration
        """
        if not index_name:
            index_name = f"idx_{table_name}_{'_'.join(columns)}"
        
        sql_statements = [
            f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table_name} ({', '.join(columns)})"
        ]
        
        rollback_sql = [
            f"DROP INDEX IF EXISTS {index_name}"
        ]
        
        metadata = {
            'type': 'index_creation',
            'table': table_name,
            'columns': columns,
            'index_name': index_name
        }
        
        return {
            'migration_name': f'add_index_{index_name}',
            'sql_statements': sql_statements,
            'rollback_sql': rollback_sql,
            'metadata': metadata
        }
    
    def drop_index_migration(self, index_name: str) -> Dict[str, Any]:
        """
        Create a migration for dropping an index.
        
        Args:
            index_name: Name of the index to drop
            
        Returns:
            Migration configuration
        """
        # Get index details for rollback
        index_details = self._get_index_details(index_name)
        
        sql_statements = [
            f"DROP INDEX IF EXISTS {index_name}"
        ]
        
        rollback_sql = []
        if index_details:
            rollback_sql = [
                f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {index_details['table']} ({', '.join(index_details['columns'])})"
            ]
        
        metadata = {
            'type': 'index_drop',
            'index_name': index_name,
            'index_details': index_details
        }
        
        return {
            'migration_name': f'drop_index_{index_name}',
            'sql_statements': sql_statements,
            'rollback_sql': rollback_sql,
            'metadata': metadata
        }
    
    def _get_index_details(self, index_name: str) -> Optional[Dict[str, Any]]:
        """Get details of an existing index."""
        try:
            # This is a simplified version - in practice, you'd query pg_indexes
            query = text("""
                SELECT 
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE indexname = :index_name
            """)
            
            result = self.db.execute(query, {'index_name': index_name})
            row = result.fetchone()
            
            if row:
                # Parse index definition to extract columns
                # This is a simplified parser
                indexdef = row.indexdef
                if 'ON' in indexdef and '(' in indexdef:
                    parts = indexdef.split('ON')
                    if len(parts) > 1:
                        table_part = parts[1].strip()
                        table_name = table_part.split('(')[0].strip()
                        columns_part = indexdef.split('(')[1].split(')')[0]
                        columns = [col.strip() for col in columns_part.split(',')]
                        
                        return {
                            'table': table_name,
                            'columns': columns,
                            'definition': indexdef
                        }
            
            return None
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting index details: {e}")
            return None

class ConstraintMigration:
    """Constraint-specific migration utilities."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def add_unique_constraint_migration(
        self, 
        table_name: str, 
        columns: List[str], 
        constraint_name: str = None
    ) -> Dict[str, Any]:
        """
        Create a migration for adding a unique constraint.
        
        Args:
            table_name: Name of the table
            columns: List of columns for the constraint
            constraint_name: Optional custom constraint name
            
        Returns:
            Migration configuration
        """
        if not constraint_name:
            constraint_name = f"uq_{table_name}_{'_'.join(columns)}"
        
        sql_statements = [
            f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} UNIQUE ({', '.join(columns)})"
        ]
        
        rollback_sql = [
            f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
        ]
        
        metadata = {
            'type': 'unique_constraint',
            'table': table_name,
            'columns': columns,
            'constraint_name': constraint_name
        }
        
        return {
            'migration_name': f'add_unique_constraint_{constraint_name}',
            'sql_statements': sql_statements,
            'rollback_sql': rollback_sql,
            'metadata': metadata
        }
    
    def add_check_constraint_migration(
        self, 
        table_name: str, 
        constraint_name: str, 
        check_condition: str
    ) -> Dict[str, Any]:
        """
        Create a migration for adding a check constraint.
        
        Args:
            table_name: Name of the table
            constraint_name: Name of the constraint
            check_condition: SQL condition for the check constraint
            
        Returns:
            Migration configuration
        """
        sql_statements = [
            f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} CHECK ({check_condition})"
        ]
        
        rollback_sql = [
            f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
        ]
        
        metadata = {
            'type': 'check_constraint',
            'table': table_name,
            'constraint_name': constraint_name,
            'condition': check_condition
        }
        
        return {
            'migration_name': f'add_check_constraint_{constraint_name}',
            'sql_statements': sql_statements,
            'rollback_sql': rollback_sql,
            'metadata': metadata
        }

# Predefined migrations for HealthMate
def get_healthmate_migrations() -> List[Dict[str, Any]]:
    """Get predefined migrations for HealthMate database optimization."""
    
    migrations = []
    
    # Index migrations for performance optimization
    index_migrations = [
        # Users table indexes
        {
            'name': 'add_users_email_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)"],
            'rollback': ["DROP INDEX IF EXISTS idx_users_email"],
            'metadata': {'type': 'index', 'table': 'users', 'columns': ['email']}
        },
        {
            'name': 'add_users_role_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role ON users(role)"],
            'rollback': ["DROP INDEX IF EXISTS idx_users_role"],
            'metadata': {'type': 'index', 'table': 'users', 'columns': ['role']}
        },
        {
            'name': 'add_users_created_at_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at)"],
            'rollback': ["DROP INDEX IF EXISTS idx_users_created_at"],
            'metadata': {'type': 'index', 'table': 'users', 'columns': ['created_at']}
        },
        
        # Health data table indexes
        {
            'name': 'add_health_data_user_type_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_data_user_type ON health_data(user_id, data_type)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_data_user_type"],
            'metadata': {'type': 'index', 'table': 'health_data', 'columns': ['user_id', 'data_type']}
        },
        {
            'name': 'add_health_data_timestamp_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_data_timestamp ON health_data(timestamp)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_data_timestamp"],
            'metadata': {'type': 'index', 'table': 'health_data', 'columns': ['timestamp']}
        },
        {
            'name': 'add_health_data_user_timestamp_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_data_user_timestamp ON health_data(user_id, timestamp)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_data_user_timestamp"],
            'metadata': {'type': 'index', 'table': 'health_data', 'columns': ['user_id', 'timestamp']}
        },
        
        # Symptom logs table indexes
        {
            'name': 'add_symptom_logs_user_timestamp_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_symptom_logs_user_timestamp ON symptom_logs(user_id, timestamp)"],
            'rollback': ["DROP INDEX IF EXISTS idx_symptom_logs_user_timestamp"],
            'metadata': {'type': 'index', 'table': 'symptom_logs', 'columns': ['user_id', 'timestamp']}
        },
        {
            'name': 'add_symptom_logs_severity_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_symptom_logs_severity ON symptom_logs(severity)"],
            'rollback': ["DROP INDEX IF EXISTS idx_symptom_logs_severity"],
            'metadata': {'type': 'index', 'table': 'symptom_logs', 'columns': ['severity']}
        },
        
        # Medication logs table indexes
        {
            'name': 'add_medication_logs_user_taken_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medication_logs_user_taken ON medication_logs(user_id, taken_at)"],
            'rollback': ["DROP INDEX IF EXISTS idx_medication_logs_user_taken"],
            'metadata': {'type': 'index', 'table': 'medication_logs', 'columns': ['user_id', 'taken_at']}
        },
        {
            'name': 'add_medication_logs_name_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_medication_logs_name ON medication_logs(medication_name)"],
            'rollback': ["DROP INDEX IF EXISTS idx_medication_logs_name"],
            'metadata': {'type': 'index', 'table': 'medication_logs', 'columns': ['medication_name']}
        },
        
        # Health goals table indexes
        {
            'name': 'add_health_goals_user_active_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_goals_user_active ON health_goals(user_id, is_active)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_goals_user_active"],
            'metadata': {'type': 'index', 'table': 'health_goals', 'columns': ['user_id', 'is_active']}
        },
        {
            'name': 'add_health_goals_type_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_goals_type ON health_goals(goal_type)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_goals_type"],
            'metadata': {'type': 'index', 'table': 'health_goals', 'columns': ['goal_type']}
        },
        
        # Health alerts table indexes
        {
            'name': 'add_health_alerts_user_acknowledged_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_alerts_user_acknowledged ON health_alerts(user_id, acknowledged)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_alerts_user_acknowledged"],
            'metadata': {'type': 'index', 'table': 'health_alerts', 'columns': ['user_id', 'acknowledged']}
        },
        {
            'name': 'add_health_alerts_triggered_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_alerts_triggered ON health_alerts(triggered_at)"],
            'rollback': ["DROP INDEX IF EXISTS idx_health_alerts_triggered"],
            'metadata': {'type': 'index', 'table': 'health_alerts', 'columns': ['triggered_at']}
        },
        
        # Conversations table indexes
        {
            'name': 'add_conversations_user_timestamp_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_user_timestamp ON conversations(user_id, timestamp)"],
            'rollback': ["DROP INDEX IF EXISTS idx_conversations_user_timestamp"],
            'metadata': {'type': 'index', 'table': 'conversations', 'columns': ['user_id', 'timestamp']}
        },
        {
            'name': 'add_conversations_feedback_index',
            'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_feedback ON conversations(feedback)"],
            'rollback': ["DROP INDEX IF EXISTS idx_conversations_feedback"],
            'metadata': {'type': 'index', 'table': 'conversations', 'columns': ['feedback']}
        }
    ]
    
    # Constraint migrations for data integrity
    constraint_migrations = [
        # Check constraints for data validation
        {
            'name': 'add_health_data_confidence_check',
            'sql': ["ALTER TABLE health_data ADD CONSTRAINT chk_health_data_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)"],
            'rollback': ["ALTER TABLE health_data DROP CONSTRAINT chk_health_data_confidence"],
            'metadata': {'type': 'check_constraint', 'table': 'health_data', 'condition': 'confidence >= 0.0 AND confidence <= 1.0'}
        },
        {
            'name': 'add_symptom_logs_pain_level_check',
            'sql': ["ALTER TABLE symptom_logs ADD CONSTRAINT chk_symptom_logs_pain_level CHECK (pain_level >= 0 AND pain_level <= 10)"],
            'rollback': ["ALTER TABLE symptom_logs DROP CONSTRAINT chk_symptom_logs_pain_level"],
            'metadata': {'type': 'check_constraint', 'table': 'symptom_logs', 'condition': 'pain_level >= 0 AND pain_level <= 10'}
        },
        {
            'name': 'add_medication_logs_effectiveness_check',
            'sql': ["ALTER TABLE medication_logs ADD CONSTRAINT chk_medication_logs_effectiveness CHECK (effectiveness >= 1 AND effectiveness <= 10)"],
            'rollback': ["ALTER TABLE medication_logs DROP CONSTRAINT chk_medication_logs_effectiveness"],
            'metadata': {'type': 'check_constraint', 'table': 'medication_logs', 'condition': 'effectiveness >= 1 AND effectiveness <= 10'}
        },
        {
            'name': 'add_health_goals_progress_check',
            'sql': ["ALTER TABLE health_goals ADD CONSTRAINT chk_health_goals_progress CHECK (progress >= 0.0 AND progress <= 100.0)"],
            'rollback': ["ALTER TABLE health_goals DROP CONSTRAINT chk_health_goals_progress"],
            'metadata': {'type': 'check_constraint', 'table': 'health_goals', 'condition': 'progress >= 0.0 AND progress <= 100.0'}
        }
    ]
    
    migrations.extend(index_migrations)
    migrations.extend(constraint_migrations)
    
    return migrations

def run_database_optimization_migrations(db_session: Session) -> Dict[str, Any]:
    """
    Run all database optimization migrations.
    
    Args:
        db_session: Database session
        
    Returns:
        Migration results
    """
    migration_manager = DatabaseMigration(db_session)
    migration_manager.create_migration_table()
    
    results = {
        'applied': [],
        'skipped': [],
        'failed': [],
        'total_migrations': 0
    }
    
    migrations = get_healthmate_migrations()
    results['total_migrations'] = len(migrations)
    
    for migration in migrations:
        migration_name = migration['name']
        
        if migration_manager.is_migration_applied(migration_name):
            results['skipped'].append(migration_name)
            logger.info(f"Migration {migration_name} already applied, skipping")
            continue
        
        result = migration_manager.apply_migration(
            migration_name=migration_name,
            sql_statements=migration['sql'],
            rollback_sql=migration['rollback'],
            metadata=migration['metadata']
        )
        
        if result['success']:
            results['applied'].append(migration_name)
            logger.info(f"Migration {migration_name} applied successfully")
        else:
            results['failed'].append({
                'name': migration_name,
                'error': result.get('error', result['message'])
            })
            logger.error(f"Migration {migration_name} failed: {result.get('error', result['message'])}")
    
    return results 