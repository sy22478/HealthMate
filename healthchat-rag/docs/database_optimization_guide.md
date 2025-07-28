# Database Optimization Guide for HealthMate

This guide provides comprehensive documentation for the database optimization features implemented in HealthMate, including index optimization, query performance analysis, database constraints, and migration management.

## Table of Contents

1. [Overview](#overview)
2. [Database Optimization Module](#database-optimization-module)
3. [Database Migration System](#database-migration-system)
4. [Database Constraints and Validations](#database-constraints-and-validations)
5. [API Endpoints](#api-endpoints)
6. [Usage Examples](#usage-examples)
7. [Performance Monitoring](#performance-monitoring)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The database optimization system in HealthMate provides comprehensive tools for:

- **Index Analysis and Optimization**: Automatic detection of missing indexes and optimization recommendations
- **Query Performance Analysis**: Identification and analysis of slow queries
- **Database Constraints**: Data integrity validation and constraint management
- **Migration Management**: Automated database schema migrations with rollback capabilities
- **Performance Monitoring**: Real-time performance metrics tracking and trending

## Database Optimization Module

### Core Components

#### DatabaseOptimizer Class

The main optimization class that provides comprehensive database analysis capabilities.

```python
from app.models.database_optimization import DatabaseOptimizer

# Initialize optimizer
optimizer = DatabaseOptimizer(db_session)

# Generate comprehensive report
report = optimizer.generate_optimization_report()
```

#### Key Features

1. **Index Analysis**
   - Analyzes existing indexes for all tables
   - Identifies missing indexes based on query patterns
   - Provides priority-based recommendations
   - Estimates impact of index creation

2. **Query Performance Analysis**
   - Analyzes slow queries using PostgreSQL statistics
   - Provides performance recommendations
   - Tracks query execution patterns
   - Identifies optimization opportunities

3. **Connection Pooling Optimization**
   - Monitors connection usage patterns
   - Provides connection pool recommendations
   - Tracks connection leaks and idle transactions
   - Optimizes pool settings

4. **Performance Monitoring**
   - Records performance metrics
   - Tracks trends over time
   - Provides historical analysis
   - Generates performance reports

### Index Optimization

#### Query Pattern Analysis

The system analyzes common query patterns for each table:

```python
# Example query patterns for users table
patterns = [
    {'columns': ['email'], 'type': 'equality', 'frequency': 'high'},
    {'columns': ['role'], 'type': 'equality', 'frequency': 'medium'},
    {'columns': ['created_at'], 'type': 'range', 'frequency': 'medium'},
    {'columns': ['is_active'], 'type': 'equality', 'frequency': 'high'}
]
```

#### Index Recommendations

The system generates intelligent index recommendations based on:

- **Query Frequency**: How often queries are executed
- **Column Selectivity**: Number of distinct values in columns
- **Query Type**: Equality, range, or composite queries
- **Table Size**: Impact of index on large tables

#### Priority Levels

- **High Priority**: Frequently used queries with high impact
- **Medium Priority**: Moderate usage with good impact
- **Low Priority**: Infrequent queries or low impact

### Slow Query Analysis

#### Performance Metrics

The system tracks various performance metrics:

- **Execution Time**: Query execution duration
- **I/O Operations**: Disk read/write operations
- **Cache Hit Ratio**: Memory cache efficiency
- **Temporary File Usage**: Query complexity indicators

#### Recommendations

Based on analysis, the system provides recommendations:

- **Add Indexes**: For high I/O operations
- **Optimize Queries**: For complex query patterns
- **Increase Cache**: For low cache hit ratios
- **Connection Pooling**: For connection management issues

## Database Migration System

### Migration Management

#### DatabaseMigration Class

Provides comprehensive migration management capabilities:

```python
from app.models.database_migrations import DatabaseMigration

# Initialize migration manager
migration_manager = DatabaseMigration(db_session)

# Apply migration
result = migration_manager.apply_migration(
    migration_name='add_users_email_index',
    sql_statements=['CREATE INDEX idx_users_email ON users(email)'],
    rollback_sql=['DROP INDEX idx_users_email']
)
```

#### Migration Features

1. **Migration Tracking**
   - Tracks applied migrations in database
   - Prevents duplicate migrations
   - Records execution time and status
   - Stores rollback information

2. **Rollback Capabilities**
   - Automatic rollback SQL generation
   - Safe migration reversal
   - Dependency-aware rollbacks
   - Transaction safety

3. **Background Execution**
   - Non-blocking migration execution
   - Progress tracking
   - Error handling and recovery
   - Status monitoring

### Predefined Migrations

The system includes predefined migrations for common optimizations:

#### Index Migrations

```python
# Users table indexes
{
    'name': 'add_users_email_index',
    'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email ON users(email)"],
    'rollback': ["DROP INDEX IF EXISTS idx_users_email"]
}

# Health data table indexes
{
    'name': 'add_health_data_user_type_index',
    'sql': ["CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_health_data_user_type ON health_data(user_id, data_type)"],
    'rollback': ["DROP INDEX IF EXISTS idx_health_data_user_type"]
}
```

#### Constraint Migrations

```python
# Check constraints for data validation
{
    'name': 'add_health_data_confidence_check',
    'sql': ["ALTER TABLE health_data ADD CONSTRAINT chk_health_data_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0)"],
    'rollback': ["ALTER TABLE health_data DROP CONSTRAINT chk_health_data_confidence"]
}
```

## Database Constraints and Validations

### Constraint Management

#### DatabaseConstraints Class

Provides comprehensive constraint validation:

```python
from app.models.database_constraints import DatabaseConstraints

# Initialize constraints manager
constraints = DatabaseConstraints(db_session)

# Validate table integrity
validation_results = constraints.validate_data_integrity('users')
```

#### Validation Types

1. **Null Constraint Validation**
   - Checks for null values in non-nullable columns
   - Identifies data integrity issues
   - Provides detailed error reporting

2. **Unique Constraint Validation**
   - Detects duplicate values in unique columns
   - Identifies constraint violations
   - Provides duplicate data analysis

3. **Foreign Key Validation**
   - Checks referential integrity
   - Identifies orphaned records
   - Validates relationship consistency

4. **Data Format Validation**
   - Validates email formats
   - Checks date ranges and formats
   - Validates numeric ranges
   - Ensures enum value compliance

### Data Validators

#### Validation Utilities

```python
from app.models.database_constraints import DataValidators

# Email validation
is_valid = DataValidators.validate_email('user@example.com')

# Phone validation
is_valid = DataValidators.validate_phone('+1-234-567-8900')

# Health metric validation
is_valid = DataValidators.validate_health_metric_value(120, 'blood_pressure')
```

#### Health Data Validation

The system includes specialized validators for health data:

- **Blood Pressure**: Positive values only
- **Heart Rate**: 30-250 bpm range
- **Weight**: 10-500 kg range
- **Temperature**: 30-45°C range
- **Blood Sugar**: 20-800 mg/dL range

### Constraint Enforcement

#### ConstraintEnforcement Class

Provides runtime constraint enforcement:

```python
from app.models.database_constraints import ConstraintEnforcement

# Initialize enforcement
enforcement = ConstraintEnforcement(db_session)

# Validate user data
errors = enforcement.enforce_user_constraints(user_data)
```

## API Endpoints

### Database Optimization Endpoints

All endpoints are prefixed with `/database` and require appropriate role permissions.

#### Analysis Endpoints

```http
GET /database/analysis/overview
GET /database/analysis/tables/{table_name}
GET /database/analysis/slow-queries?time_threshold_ms=1000
GET /database/analysis/connection-pooling
```

#### Migration Endpoints

```http
POST /database/migrations/run
GET /database/migrations/status
POST /database/migrations/rollback/{migration_name}
```

#### Constraint Endpoints

```http
GET /database/constraints/validation
GET /database/constraints/tables/{table_name}
```

#### Performance Endpoints

```http
GET /database/performance/trends/{metric_name}?days=7&table_name=users
POST /database/performance/metrics
GET /database/health
```

### Authentication and Authorization

All endpoints require authentication and appropriate role permissions:

- **Admin Role**: Full access to all endpoints
- **Researcher Role**: Read access to analysis and monitoring endpoints
- **Patient/Doctor Roles**: No access to optimization endpoints

## Usage Examples

### Running Database Analysis

```python
from app.models.database_optimization import analyze_database_performance

# Perform comprehensive analysis
report = analyze_database_performance(db_session)

# Access analysis results
index_recommendations = report['index_analysis']
slow_queries = report['slow_queries']
connection_analysis = report['connection_pooling']
```

### Applying Optimizations

```python
from app.models.database_migrations import run_database_optimization_migrations

# Run all optimization migrations
results = run_database_optimization_migrations(db_session)

# Check results
applied_migrations = results['applied']
failed_migrations = results['failed']
```

### Validating Data Integrity

```python
from app.models.database_constraints import validate_database_integrity

# Validate all tables
validation_results = validate_database_integrity(db_session)

# Check overall status
overall_status = validation_results['overall_status']
total_errors = validation_results['total_errors']
```

### Recording Performance Metrics

```python
from app.models.database_optimization import DatabaseOptimizer

optimizer = DatabaseOptimizer(db_session)

# Record query execution time
optimizer.record_performance_metric(
    metric_name='query_execution_time',
    metric_value=150.5,
    metric_unit='ms',
    table_name='users'
)
```

## Performance Monitoring

### Metrics Tracking

The system automatically tracks various performance metrics:

1. **Query Performance**
   - Execution time
   - I/O operations
   - Cache hit ratios
   - Temporary file usage

2. **Index Usage**
   - Index hit rates
   - Missing index recommendations
   - Index creation impact

3. **Connection Pooling**
   - Active connections
   - Idle connections
   - Connection leaks
   - Pool efficiency

4. **Data Integrity**
   - Constraint violations
   - Data format errors
   - Foreign key issues

### Trend Analysis

```python
# Get performance trends
trends = optimizer.get_performance_trends(
    metric_name='query_execution_time',
    days=7,
    table_name='users'
)

# Analyze trends
for trend in trends:
    print(f"Date: {trend['date']}")
    print(f"Average: {trend['avg_value']}")
    print(f"Min: {trend['min_value']}")
    print(f"Max: {trend['max_value']}")
```

### Health Monitoring

```python
# Get database health status
health_status = optimizer.get_database_health_status()

# Check overall health
if health_status['overall_status'] == 'healthy':
    print("Database is healthy")
elif health_status['overall_status'] == 'warning':
    print("Database has warnings")
else:
    print("Database has issues")
```

## Best Practices

### Index Optimization

1. **Analyze Query Patterns**
   - Identify frequently used queries
   - Understand query types (equality, range, composite)
   - Consider query frequency and impact

2. **Prioritize Indexes**
   - Focus on high-priority recommendations first
   - Consider table size and update frequency
   - Balance performance gains vs. maintenance overhead

3. **Monitor Index Usage**
   - Track index hit rates
   - Remove unused indexes
   - Optimize existing indexes

### Migration Management

1. **Test Migrations**
   - Always test migrations in development
   - Verify rollback procedures
   - Check data integrity after migrations

2. **Backup Before Migrations**
   - Create database backups before major migrations
   - Test migration procedures on backup data
   - Have rollback plans ready

3. **Monitor Migration Progress**
   - Track migration execution time
   - Monitor system performance during migrations
   - Handle migration failures gracefully

### Performance Monitoring

1. **Set Up Regular Monitoring**
   - Schedule regular performance analysis
   - Track key performance indicators
   - Set up alerts for performance issues

2. **Analyze Trends**
   - Monitor performance trends over time
   - Identify performance degradation patterns
   - Plan capacity based on trends

3. **Optimize Based on Data**
   - Use performance data to guide optimizations
   - Focus on high-impact improvements
   - Continuously iterate and improve

## Troubleshooting

### Common Issues

#### Import Errors

```python
# If you encounter import errors, check:
# 1. Database connection
# 2. Required dependencies
# 3. RBAC configuration

# Test import
try:
    from app.models.database_optimization import DatabaseOptimizer
    print("Import successful")
except ImportError as e:
    print(f"Import error: {e}")
```

#### Permission Errors

```python
# Ensure proper role permissions
# Admin role required for:
# - Running migrations
# - Rollback operations
# - System-level optimizations

# Researcher role can:
# - View analysis results
# - Monitor performance
# - Access read-only endpoints
```

#### Database Connection Issues

```python
# Check database connectivity
try:
    optimizer = DatabaseOptimizer(db_session)
    print("Database connection successful")
except Exception as e:
    print(f"Database connection error: {e}")
```

### Performance Issues

#### Slow Query Analysis

```python
# Analyze slow queries
slow_queries = optimizer.analyze_slow_queries(time_threshold_ms=1000)

# Check recommendations
for query in slow_queries:
    print(f"Query: {query['query']}")
    print(f"Mean time: {query['mean_time']}ms")
    print(f"Recommendations: {query['recommendations']}")
```

#### Index Issues

```python
# Check index recommendations
analysis = optimizer.analyze_table_indexes('users')
recommendations = analysis['recommendations']

# Apply high-priority recommendations
for rec in recommendations:
    if rec['priority'] == 'high':
        print(f"High priority: {rec['columns']}")
```

### Data Integrity Issues

```python
# Validate data integrity
validation = validate_database_integrity(db_session)

# Check for errors
if validation['total_errors'] > 0:
    print("Data integrity issues found:")
    for table, results in validation['tables'].items():
        for error in results.get('errors', []):
            print(f"Table {table}: {error['message']}")
```

## Conclusion

The database optimization system in HealthMate provides comprehensive tools for maintaining and improving database performance. By following the guidelines and best practices outlined in this guide, you can ensure optimal database performance and data integrity for your HealthMate application.

For additional support or questions, refer to the API documentation or contact the development team. 