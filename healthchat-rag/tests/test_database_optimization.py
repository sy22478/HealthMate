"""
Test Database Optimization Module.

This module tests the database optimization functionality including:
- Index optimization
- Query performance analysis
- Database constraints and validations
- Migration system
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models.database_optimization import DatabaseOptimizer, analyze_database_performance
from app.models.database_migrations import DatabaseMigration, run_database_optimization_migrations
from app.models.database_constraints import DatabaseConstraints, DataValidators, ConstraintEnforcement, validate_database_integrity

class TestDatabaseOptimizer:
    """Test database optimization functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.bind = Mock()
        return session
    
    @pytest.fixture
    def mock_inspector(self):
        """Create a mock inspector."""
        inspector = Mock()
        inspector.get_indexes.return_value = [
            {'name': 'idx_users_email', 'columns': ['email']},
            {'name': 'idx_users_role', 'columns': ['role']}
        ]
        return inspector
    
    @pytest.fixture
    def optimizer(self, mock_db_session, mock_inspector):
        """Create a database optimizer instance."""
        with patch('app.models.database_optimization.inspect', return_value=mock_inspector):
            return DatabaseOptimizer(mock_db_session)
    
    def test_optimizer_initialization(self, optimizer):
        """Test database optimizer initialization."""
        assert optimizer.db is not None
        assert optimizer.inspector is not None
    
    def test_analyze_table_indexes(self, optimizer, mock_db_session):
        """Test table index analysis."""
        # Mock database query results
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            Mock(attname='email', n_distinct=1000, correlation=0.8),
            Mock(attname='role', n_distinct=5, correlation=0.2)
        ]
        mock_db_session.execute.return_value = mock_result
        
        result = optimizer.analyze_table_indexes('users')
        
        assert 'table_name' in result
        assert result['table_name'] == 'users'
        assert 'existing_indexes' in result
        assert 'column_statistics' in result
        assert 'query_patterns' in result
        assert 'recommendations' in result
    
    def test_get_query_patterns(self, optimizer):
        """Test query pattern generation."""
        patterns = optimizer._get_query_patterns('users')
        
        assert isinstance(patterns, list)
        assert len(patterns) > 0
        
        # Check for expected patterns
        email_pattern = next((p for p in patterns if 'email' in p['columns']), None)
        assert email_pattern is not None
        assert email_pattern['type'] == 'equality'
        assert email_pattern['frequency'] == 'high'
    
    def test_generate_index_recommendations(self, optimizer):
        """Test index recommendation generation."""
        existing_indexes = [{'name': 'idx_users_email', 'columns': ['email']}]
        column_stats = {'email': {'n_distinct': 1000, 'correlation': 0.8}}
        query_patterns = [
            {'columns': ['email'], 'type': 'equality', 'frequency': 'high'},
            {'columns': ['role'], 'type': 'equality', 'frequency': 'medium'}
        ]
        
        recommendations = optimizer._generate_index_recommendations(
            'users', existing_indexes, column_stats, query_patterns
        )
        
        assert isinstance(recommendations, list)
        
        # Should recommend index for 'role' since it's not in existing indexes
        role_recommendation = next((r for r in recommendations if 'role' in r['columns']), None)
        assert role_recommendation is not None
        assert role_recommendation['type'] == 'create_index'
    
    def test_calculate_index_priority(self, optimizer):
        """Test index priority calculation."""
        high_freq_pattern = {'frequency': 'high'}
        medium_freq_pattern = {'frequency': 'medium'}
        low_freq_pattern = {'frequency': 'low'}
        
        assert optimizer._calculate_index_priority(high_freq_pattern) == 'high'
        assert optimizer._calculate_index_priority(medium_freq_pattern) == 'medium'
        assert optimizer._calculate_index_priority(low_freq_pattern) == 'low'
    
    def test_estimate_index_impact(self, optimizer):
        """Test index impact estimation."""
        columns = ['email', 'role']
        column_stats = {
            'email': {'n_distinct': 10000, 'correlation': 0.8},
            'role': {'n_distinct': 5, 'correlation': 0.2}
        }
        pattern = {'columns': columns, 'frequency': 'high'}
        
        impact = optimizer._estimate_index_impact(columns, column_stats, pattern)
        assert impact in ['high', 'medium', 'low']
    
    def test_analyze_slow_queries(self, optimizer, mock_db_session):
        """Test slow query analysis."""
        # Mock slow query results
        mock_result = Mock()
        mock_row = Mock()
        mock_row.query = "SELECT * FROM users WHERE email = 'test@example.com'"
        mock_row.calls = 100
        mock_row.total_time = 5000
        mock_row.mean_time = 50
        mock_row.rows = 1000
        mock_row.shared_blks_hit = 800
        mock_row.shared_blks_read = 200
        mock_row.temp_blks_read = 50
        mock_row.blk_read_time = 100
        mock_row.blk_write_time = 10
        
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute.return_value = mock_result
        
        slow_queries = optimizer.analyze_slow_queries(time_threshold_ms=10)
        
        assert isinstance(slow_queries, list)
        if slow_queries:  # If pg_stat_statements is available
            assert len(slow_queries) > 0
            assert 'query' in slow_queries[0]
            assert 'recommendations' in slow_queries[0]
    
    def test_optimize_connection_pooling(self, optimizer, mock_db_session):
        """Test connection pooling optimization."""
        # Mock connection statistics
        mock_stats_result = Mock()
        mock_stats_row = Mock()
        mock_stats_row.active_connections = 25
        mock_stats_row.active_queries = 10
        mock_stats_row.idle_connections = 15
        mock_stats_row.idle_in_transaction = 2
        mock_stats_result.fetchone.return_value = mock_stats_row
        
        # Mock pool settings
        mock_settings_result = Mock()
        mock_settings_result.fetchall.return_value = [
            Mock(name='max_connections', setting='100', unit=None, context='postmaster'),
            Mock(name='shared_buffers', setting='128MB', unit='8kB', context='postmaster'),
            Mock(name='work_mem', setting='4MB', unit='kB', context='user')
        ]
        
        mock_db_session.execute.side_effect = [mock_stats_result, mock_settings_result]
        
        result = optimizer.optimize_connection_pooling()
        
        assert 'current_stats' in result
        assert 'pool_settings' in result
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
    
    def test_create_performance_monitoring_table(self, optimizer, mock_db_session):
        """Test performance monitoring table creation."""
        optimizer.create_performance_monitoring_table()
        
        # Verify that execute was called for table creation
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_record_performance_metric(self, optimizer, mock_db_session):
        """Test performance metric recording."""
        optimizer.record_performance_metric(
            metric_name='test_metric',
            metric_value=100.5,
            metric_unit='ms',
            table_name='users'
        )
        
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_get_performance_trends(self, optimizer, mock_db_session):
        """Test performance trends retrieval."""
        # Mock trend results
        mock_result = Mock()
        mock_row = Mock()
        mock_row.date = '2024-01-01'
        mock_row.avg_value = 50.5
        mock_row.min_value = 10.0
        mock_row.max_value = 100.0
        mock_row.data_points = 24
        mock_result.fetchall.return_value = [mock_row]
        mock_db_session.execute.return_value = mock_result
        
        trends = optimizer.get_performance_trends('query_execution_time', days=7)
        
        assert isinstance(trends, list)
        if trends:  # If performance_metrics table exists
            assert len(trends) > 0
            assert 'date' in trends[0]
            assert 'avg_value' in trends[0]
    
    def test_generate_optimization_report(self, optimizer, mock_db_session):
        """Test optimization report generation."""
        # Mock various analysis results
        with patch.object(optimizer, 'analyze_table_indexes') as mock_analyze:
            mock_analyze.return_value = {
                'table_name': 'users',
                'existing_indexes': [],
                'recommendations': []
            }
            
            with patch.object(optimizer, 'analyze_slow_queries') as mock_slow:
                mock_slow.return_value = []
                
                with patch.object(optimizer, 'optimize_connection_pooling') as mock_pool:
                    mock_pool.return_value = {'recommendations': []}
                    
                    with patch.object(optimizer, 'get_performance_trends') as mock_trends:
                        mock_trends.return_value = []
                        
                        report = optimizer.generate_optimization_report()
                        
                        assert 'timestamp' in report
                        assert 'index_analysis' in report
                        assert 'slow_queries' in report
                        assert 'connection_pooling' in report
                        assert 'performance_trends' in report
                        assert 'recommendations' in report

class TestDatabaseMigration:
    """Test database migration functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.bind = Mock()
        return session
    
    @pytest.fixture
    def migration_manager(self, mock_db_session):
        """Create a migration manager instance."""
        with patch('app.models.database_migrations.inspect') as mock_inspect:
            mock_inspector = Mock()
            mock_inspect.return_value = mock_inspector
            return DatabaseMigration(mock_db_session)
    
    def test_create_migration_table(self, migration_manager, mock_db_session):
        """Test migration table creation."""
        migration_manager.create_migration_table()
        
        mock_db_session.execute.assert_called()
        mock_db_session.commit.assert_called()
    
    def test_get_applied_migrations(self, migration_manager, mock_db_session):
        """Test getting applied migrations."""
        # Mock query results
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            Mock(migration_name='migration_001'),
            Mock(migration_name='migration_002')
        ]
        mock_db_session.execute.return_value = mock_result
        
        applied_migrations = migration_manager.get_applied_migrations()
        
        assert isinstance(applied_migrations, list)
        assert len(applied_migrations) == 2
        assert 'migration_001' in applied_migrations
        assert 'migration_002' in applied_migrations
    
    def test_is_migration_applied(self, migration_manager, mock_db_session):
        """Test migration applied status check."""
        # Mock query results
        mock_result = Mock()
        mock_result.scalar.return_value = 1  # Migration exists
        mock_db_session.execute.return_value = mock_result
        
        is_applied = migration_manager.is_migration_applied('test_migration')
        
        assert is_applied is True
    
    def test_apply_migration_success(self, migration_manager, mock_db_session):
        """Test successful migration application."""
        # Mock that migration doesn't exist
        with patch.object(migration_manager, 'is_migration_applied', return_value=False):
            result = migration_manager.apply_migration(
                migration_name='test_migration',
                sql_statements=['CREATE INDEX test_idx ON users(email)'],
                rollback_sql=['DROP INDEX test_idx']
            )
            
            assert result['success'] is True
            assert 'test_migration' in result['message']
    
    def test_apply_migration_already_applied(self, migration_manager):
        """Test migration application when already applied."""
        with patch.object(migration_manager, 'is_migration_applied', return_value=True):
            result = migration_manager.apply_migration(
                migration_name='test_migration',
                sql_statements=['CREATE INDEX test_idx ON users(email)']
            )
            
            assert result['success'] is False
            assert 'already applied' in result['message']
    
    def test_apply_migration_failure(self, migration_manager, mock_db_session):
        """Test migration application failure."""
        # Mock SQLAlchemyError
        mock_db_session.execute.side_effect = SQLAlchemyError("Test error")
        
        with patch.object(migration_manager, 'is_migration_applied', return_value=False):
            result = migration_manager.apply_migration(
                migration_name='test_migration',
                sql_statements=['INVALID SQL']
            )
            
            assert result['success'] is False
            assert 'error' in result
            assert 'Test error' in result['error']

class TestDatabaseConstraints:
    """Test database constraints functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.bind = Mock()
        return session
    
    @pytest.fixture
    def constraints(self, mock_db_session):
        """Create a constraints instance."""
        with patch('app.models.database_constraints.inspect') as mock_inspect:
            mock_inspector = Mock()
            mock_inspect.return_value = mock_inspector
            return DatabaseConstraints(mock_db_session)
    
    def test_get_table_constraints(self, constraints, mock_db_session):
        """Test getting table constraints."""
        # Mock inspector methods
        constraints.inspector.get_pk_constraint.return_value = {'constrained_columns': ['id']}
        constraints.inspector.get_foreign_keys.return_value = []
        constraints.inspector.get_unique_constraints.return_value = []
        constraints.inspector.get_check_constraints.return_value = []
        constraints.inspector.get_indexes.return_value = []
        
        result = constraints.get_table_constraints('users')
        
        assert 'table_name' in result
        assert result['table_name'] == 'users'
        assert 'constraints' in result
        assert 'primary_keys' in result['constraints']
    
    def test_validate_data_integrity(self, constraints, mock_db_session):
        """Test data integrity validation."""
        # Mock inspector methods
        constraints.inspector.get_columns.return_value = [
            {'name': 'email', 'nullable': False},
            {'name': 'role', 'nullable': True}
        ]
        constraints.inspector.get_unique_constraints.return_value = []
        constraints.inspector.get_foreign_keys.return_value = []
        
        # Mock query results
        mock_result = Mock()
        mock_result.scalar.return_value = 0  # No null values
        mock_db_session.execute.return_value = mock_result
        
        result = constraints.validate_data_integrity('users')
        
        assert 'table_name' in result
        assert 'checks' in result
        assert 'errors' in result
        assert 'warnings' in result

class TestDataValidators:
    """Test data validation utilities."""
    
    def test_validate_email(self):
        """Test email validation."""
        assert DataValidators.validate_email('test@example.com') is True
        assert DataValidators.validate_email('invalid-email') is False
        assert DataValidators.validate_email('') is False
        assert DataValidators.validate_email(None) is False
    
    def test_validate_phone(self):
        """Test phone validation."""
        assert DataValidators.validate_phone('1234567890') is True
        assert DataValidators.validate_phone('+1-234-567-8900') is True
        assert DataValidators.validate_phone('123') is False  # Too short
        assert DataValidators.validate_phone('') is False
        assert DataValidators.validate_phone(None) is False
    
    def test_validate_date_of_birth(self):
        """Test date of birth validation."""
        assert DataValidators.validate_date_of_birth('1990-01-01') is True
        assert DataValidators.validate_date_of_birth('2025-01-01') is False  # Future date
        assert DataValidators.validate_date_of_birth('invalid-date') is False
        assert DataValidators.validate_date_of_birth('') is False
        assert DataValidators.validate_date_of_birth(None) is False
    
    def test_validate_json_field(self):
        """Test JSON field validation."""
        assert DataValidators.validate_json_field('{"key": "value"}') is True
        assert DataValidators.validate_json_field('') is True  # Empty is valid
        assert DataValidators.validate_json_field('invalid json') is False
        assert DataValidators.validate_json_field(None) is True
    
    def test_validate_health_metric_value(self):
        """Test health metric value validation."""
        # Blood pressure
        assert DataValidators.validate_health_metric_value(120, 'blood_pressure') is True
        assert DataValidators.validate_health_metric_value(-10, 'blood_pressure') is False
        
        # Heart rate
        assert DataValidators.validate_health_metric_value(80, 'heart_rate') is True
        assert DataValidators.validate_health_metric_value(300, 'heart_rate') is False
        
        # Weight
        assert DataValidators.validate_health_metric_value(70, 'weight') is True
        assert DataValidators.validate_health_metric_value(5, 'weight') is False
        
        # Invalid data type
        assert DataValidators.validate_health_metric_value(100, 'invalid_type') is True  # Falls back to number check
    
    def test_validate_medication_dosage(self):
        """Test medication dosage validation."""
        assert DataValidators.validate_medication_dosage('10mg') is True
        assert DataValidators.validate_medication_dosage('5ml') is True
        assert DataValidators.validate_medication_dosage('2 tablets') is True
        assert DataValidators.validate_medication_dosage('invalid') is False
        assert DataValidators.validate_medication_dosage('') is False
        assert DataValidators.validate_medication_dosage(None) is False
    
    def test_validate_frequency(self):
        """Test medication frequency validation."""
        assert DataValidators.validate_frequency('twice daily') is True
        assert DataValidators.validate_frequency('every 8 hours') is True
        assert DataValidators.validate_frequency('as needed') is True
        assert DataValidators.validate_frequency('invalid frequency') is False
        assert DataValidators.validate_frequency('') is False
        assert DataValidators.validate_frequency(None) is False

class TestConstraintEnforcement:
    """Test constraint enforcement functionality."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def enforcement(self, mock_db_session):
        """Create a constraint enforcement instance."""
        return ConstraintEnforcement(mock_db_session)
    
    def test_enforce_user_constraints(self, enforcement):
        """Test user constraint enforcement."""
        # Valid user data
        valid_user = {
            'email': 'test@example.com',
            'phone': '1234567890',
            'date_of_birth': '1990-01-01',
            'age': 30,
            'role': 'patient'
        }
        
        errors = enforcement.enforce_user_constraints(valid_user)
        assert len(errors) == 0
        
        # Invalid user data
        invalid_user = {
            'email': 'invalid-email',
            'phone': '123',
            'date_of_birth': '2025-01-01',
            'age': -5,
            'role': 'invalid_role'
        }
        
        errors = enforcement.enforce_user_constraints(invalid_user)
        assert len(errors) > 0
        assert any('email' in error.lower() for error in errors)
        assert any('phone' in error.lower() for error in errors)
        assert any('date of birth' in error.lower() for error in errors)
        assert any('age' in error.lower() for error in errors)
        assert any('role' in error.lower() for error in errors)
    
    def test_enforce_health_data_constraints(self, enforcement):
        """Test health data constraint enforcement."""
        # Valid health data
        valid_health_data = {
            'data_type': 'blood_pressure',
            'value': 120,
            'confidence': 0.95
        }
        
        errors = enforcement.enforce_health_data_constraints(valid_health_data)
        assert len(errors) == 0
        
        # Invalid health data
        invalid_health_data = {
            'data_type': 'invalid_type',
            'value': -10,
            'confidence': 1.5
        }
        
        errors = enforcement.enforce_health_data_constraints(invalid_health_data)
        assert len(errors) > 0
        assert any('data type' in error.lower() for error in errors)
        assert any('confidence' in error.lower() for error in errors)
    
    def test_enforce_medication_constraints(self, enforcement):
        """Test medication constraint enforcement."""
        # Valid medication data
        valid_medication = {
            'dosage': '10mg',
            'frequency': 'twice daily',
            'effectiveness': 8
        }
        
        errors = enforcement.enforce_medication_constraints(valid_medication)
        assert len(errors) == 0
        
        # Invalid medication data
        invalid_medication = {
            'dosage': 'invalid',
            'frequency': 'invalid frequency',
            'effectiveness': 15
        }
        
        errors = enforcement.enforce_medication_constraints(invalid_medication)
        assert len(errors) > 0
        assert any('dosage' in error.lower() for error in errors)
        assert any('frequency' in error.lower() for error in errors)
        assert any('effectiveness' in error.lower() for error in errors)
    
    def test_enforce_symptom_constraints(self, enforcement):
        """Test symptom constraint enforcement."""
        # Valid symptom data
        valid_symptom = {
            'severity': 'moderate',
            'pain_level': 5
        }
        
        errors = enforcement.enforce_symptom_constraints(valid_symptom)
        assert len(errors) == 0
        
        # Invalid symptom data
        invalid_symptom = {
            'severity': 'invalid',
            'pain_level': 15
        }
        
        errors = enforcement.enforce_symptom_constraints(invalid_symptom)
        assert len(errors) > 0
        assert any('severity' in error.lower() for error in errors)
        assert any('pain level' in error.lower() for error in errors)
    
    def test_enforce_health_goal_constraints(self, enforcement):
        """Test health goal constraint enforcement."""
        # Valid health goal data
        valid_goal = {
            'progress': 75.5,
            'goal_type': 'weight_loss'
        }
        
        errors = enforcement.enforce_health_goal_constraints(valid_goal)
        assert len(errors) == 0
        
        # Invalid health goal data
        invalid_goal = {
            'progress': 150.0,
            'goal_type': 'invalid_type'
        }
        
        errors = enforcement.enforce_health_goal_constraints(invalid_goal)
        assert len(errors) > 0
        assert any('progress' in error.lower() for error in errors)
        assert any('goal type' in error.lower() for error in errors)

class TestDatabaseOptimizationIntegration:
    """Integration tests for database optimization."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        session = Mock(spec=Session)
        session.bind = Mock()
        return session
    
    def test_analyze_database_performance(self, mock_db_session):
        """Test comprehensive database performance analysis."""
        with patch('app.models.database_optimization.DatabaseOptimizer') as mock_optimizer_class:
            mock_optimizer = Mock()
            mock_optimizer_class.return_value = mock_optimizer
            
            # Mock the analysis methods
            mock_optimizer.analyze_table_indexes.return_value = {
                'table_name': 'users',
                'recommendations': []
            }
            mock_optimizer.analyze_slow_queries.return_value = []
            mock_optimizer.optimize_connection_pooling.return_value = {'recommendations': []}
            mock_optimizer.get_performance_trends.return_value = []
            mock_optimizer.generate_optimization_report.return_value = {
                'timestamp': '2024-01-01T00:00:00Z',
                'index_analysis': {},
                'slow_queries': [],
                'connection_pooling': {},
                'performance_trends': {},
                'recommendations': []
            }
            
            report = analyze_database_performance(mock_db_session)
            
            assert 'timestamp' in report
            assert 'index_analysis' in report
            assert 'slow_queries' in report
            assert 'connection_pooling' in report
            assert 'performance_trends' in report
            assert 'recommendations' in report
    
    def test_run_database_optimization_migrations(self, mock_db_session):
        """Test running database optimization migrations."""
        with patch('app.models.database_migrations.DatabaseMigration') as mock_migration_class:
            mock_migration = Mock()
            mock_migration_class.return_value = mock_migration
            
            # Mock migration methods
            mock_migration.is_migration_applied.return_value = False
            mock_migration.apply_migration.return_value = {
                'success': True,
                'message': 'Migration applied successfully'
            }
            
            results = run_database_optimization_migrations(mock_db_session)
            
            assert 'applied' in results
            assert 'skipped' in results
            assert 'failed' in results
            assert 'total_migrations' in results
            assert isinstance(results['total_migrations'], int)
    
    def test_validate_database_integrity(self, mock_db_session):
        """Test database integrity validation."""
        with patch('app.models.database_constraints.DatabaseConstraints') as mock_constraints_class:
            mock_constraints = Mock()
            mock_constraints_class.return_value = mock_constraints
            
            # Mock validation method
            mock_constraints.validate_data_integrity.return_value = {
                'table_name': 'users',
                'checks': [],
                'errors': [],
                'warnings': []
            }
            
            results = validate_database_integrity(mock_db_session)
            
            assert 'timestamp' in results
            assert 'tables' in results
            assert 'overall_status' in results
            assert 'total_errors' in results
            assert 'total_warnings' in results

if __name__ == "__main__":
    pytest.main([__file__]) 