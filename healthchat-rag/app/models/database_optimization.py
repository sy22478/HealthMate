"""
Database optimization utilities for HealthMate backend.

This module provides tools for:
- Database index management
- Query optimization
- Performance monitoring
- Connection pooling optimization
"""

import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, text, Index, inspect
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import time
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class QueryPerformanceMetrics:
    """Data class for storing query performance metrics."""
    query: str
    execution_time: float
    timestamp: datetime
    table_name: Optional[str] = None
    operation_type: Optional[str] = None
    rows_affected: Optional[int] = None

class DatabaseOptimizer:
    """Database optimization and performance monitoring utility."""
    
    def __init__(self, engine):
        self.engine = engine
        self.performance_log: List[QueryPerformanceMetrics] = []
    
    def create_common_indexes(self) -> Dict[str, bool]:
        """
        Create common database indexes for improved query performance.
        
        Returns:
            Dict[str, bool]: Status of index creation for each table
        """
        indexes_status = {}
        
        try:
            with self.engine.connect() as connection:
                # User table indexes
                indexes_status['users'] = self._create_user_indexes(connection)
                
                # Health data indexes
                indexes_status['health_data'] = self._create_health_data_indexes(connection)
                
                # Chat conversation indexes
                indexes_status['conversations'] = self._create_conversation_indexes(connection)
                
                # Authentication and session indexes
                indexes_status['auth_sessions'] = self._create_auth_indexes(connection)
                
                logger.info("Database indexes created successfully", extra={
                    "indexes_status": indexes_status
                })
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database indexes: {e}")
            indexes_status['error'] = str(e)
        
        return indexes_status
    
    def _create_user_indexes(self, connection) -> bool:
        """Create indexes for user table."""
        try:
            # Email index for login queries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_email 
                ON users (email)
            """))
            
            # Username index for login queries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_username 
                ON users (username)
            """))
            
            # Created at index for user analytics
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_created_at 
                ON users (created_at)
            """))
            
            # Role index for authorization queries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_role 
                ON users (role)
            """))
            
            connection.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create user indexes: {e}")
            return False
    
    def _create_health_data_indexes(self, connection) -> bool:
        """Create indexes for health data tables."""
        try:
            # User ID and timestamp index for health data queries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_health_data_user_timestamp 
                ON health_data (user_id, timestamp)
            """))
            
            # Metric type index for filtering
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_health_data_metric_type 
                ON health_data (metric_type)
            """))
            
            # Value range index for analytics queries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_health_data_value 
                ON health_data (value)
            """))
            
            # Composite index for user and metric type
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_health_data_user_metric 
                ON health_data (user_id, metric_type)
            """))
            
            connection.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create health data indexes: {e}")
            return False
    
    def _create_conversation_indexes(self, connection) -> bool:
        """Create indexes for conversation and chat tables."""
        try:
            # User ID and timestamp for conversation queries
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user_timestamp 
                ON conversations (user_id, created_at)
            """))
            
            # Message timestamp for chat history
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp 
                ON messages (conversation_id, timestamp)
            """))
            
            # Message type for filtering
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_messages_type 
                ON messages (message_type)
            """))
            
            connection.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create conversation indexes: {e}")
            return False
    
    def _create_auth_indexes(self, connection) -> bool:
        """Create indexes for authentication and session tables."""
        try:
            # Token hash index for JWT validation
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blacklisted_tokens_token_hash 
                ON blacklisted_tokens (token_hash)
            """))
            
            # User ID and expiry for session management
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_blacklisted_tokens_user_expiry 
                ON blacklisted_tokens (user_id, expires_at)
            """))
            
            connection.commit()
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to create auth indexes: {e}")
            return False
    
    def analyze_query_performance(self, query: str, params: Optional[Dict] = None) -> QueryPerformanceMetrics:
        """
        Analyze the performance of a specific query.
        
        Args:
            query: SQL query to analyze
            params: Query parameters
            
        Returns:
            QueryPerformanceMetrics: Performance metrics for the query
        """
        start_time = time.time()
        
        try:
            with self.engine.connect() as connection:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                
                execution_time = time.time() - start_time
                
                # Try to get row count
                rows_affected = None
                try:
                    if hasattr(result, 'rowcount'):
                        rows_affected = result.rowcount
                except:
                    pass
                
                metrics = QueryPerformanceMetrics(
                    query=query,
                    execution_time=execution_time,
                    timestamp=datetime.now(),
                    rows_affected=rows_affected
                )
                
                self.performance_log.append(metrics)
                
                # Log slow queries
                if execution_time > 1.0:  # Log queries taking more than 1 second
                    logger.warning("Slow query detected", extra={
                        "query": query,
                        "execution_time": execution_time,
                        "rows_affected": rows_affected
                    })
                
                return metrics
                
        except SQLAlchemyError as e:
            execution_time = time.time() - start_time
            logger.error(f"Query execution failed: {e}", extra={
                "query": query,
                "execution_time": execution_time
            })
            
            return QueryPerformanceMetrics(
                query=query,
                execution_time=execution_time,
                timestamp=datetime.now()
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of query performance metrics.
        
        Returns:
            Dict containing performance statistics
        """
        if not self.performance_log:
            return {"message": "No performance data available"}
        
        execution_times = [m.execution_time for m in self.performance_log]
        
        return {
            "total_queries": len(self.performance_log),
            "average_execution_time": sum(execution_times) / len(execution_times),
            "max_execution_time": max(execution_times),
            "min_execution_time": min(execution_times),
            "slow_queries_count": len([t for t in execution_times if t > 1.0]),
            "recent_queries": [
                {
                    "query": m.query[:100] + "..." if len(m.query) > 100 else m.query,
                    "execution_time": m.execution_time,
                    "timestamp": m.timestamp.isoformat()
                }
                for m in self.performance_log[-10:]  # Last 10 queries
            ]
        }
    
    def optimize_connection_pool(self, pool_size: int = 10, max_overflow: int = 20) -> bool:
        """
        Optimize database connection pool settings.
        
        Args:
            pool_size: Number of connections to maintain
            max_overflow: Maximum number of connections that can be created beyond pool_size
            
        Returns:
            bool: True if optimization was successful
        """
        try:
            # Recreate engine with optimized pool settings
            from app.config import settings
            
            optimized_engine = create_engine(
                settings.postgres_uri,
                pool_size=pool_size,
                max_overflow=max_overflow,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections every hour
                pool_timeout=30,    # Wait up to 30 seconds for a connection
                echo=False  # Disable SQL echoing in production
            )
            
            # Test the optimized engine
            with optimized_engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            
            # Replace the existing engine
            self.engine = optimized_engine
            
            logger.info("Database connection pool optimized successfully", extra={
                "pool_size": pool_size,
                "max_overflow": max_overflow
            })
            
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to optimize connection pool: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics and health information.
        
        Returns:
            Dict containing database statistics
        """
        try:
            with self.engine.connect() as connection:
                # Get table sizes
                table_sizes = connection.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    ORDER BY tablename, attname
                """)).fetchall()
                
                # Get index usage statistics
                index_usage = connection.execute(text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes
                    ORDER BY idx_scan DESC
                """)).fetchall()
                
                # Get connection information
                connections = connection.execute(text("""
                    SELECT 
                        count(*) as active_connections,
                        count(*) FILTER (WHERE state = 'active') as active_queries
                    FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)).fetchone()
                
                return {
                    "table_statistics": [
                        {
                            "schema": row[0],
                            "table": row[1],
                            "column": row[2],
                            "distinct_values": row[3],
                            "correlation": row[4]
                        }
                        for row in table_sizes
                    ],
                    "index_usage": [
                        {
                            "schema": row[0],
                            "table": row[1],
                            "index": row[2],
                            "scans": row[3],
                            "tuples_read": row[4],
                            "tuples_fetched": row[5]
                        }
                        for row in index_usage
                    ],
                    "connections": {
                        "active_connections": connections[0],
                        "active_queries": connections[1]
                    }
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

# Global database optimizer instance
db_optimizer = None

def get_db_optimizer():
    """Get the global database optimizer instance."""
    global db_optimizer
    if db_optimizer is None:
        from app.database import engine
        db_optimizer = DatabaseOptimizer(engine)
    return db_optimizer

@contextmanager
def query_performance_monitor(query: str, params: Optional[Dict] = None):
    """
    Context manager for monitoring query performance.
    
    Usage:
        with query_performance_monitor("SELECT * FROM users WHERE id = :id", {"id": 1}) as metrics:
            # Execute your query here
            pass
    """
    optimizer = get_db_optimizer()
    metrics = optimizer.analyze_query_performance(query, params)
    yield metrics 