"""
Load Balancing Utilities for HealthMate Backend.

This module provides:
- Database read replica load balancing
- Connection pooling and management
- Health check monitoring
- Failover handling
- Query routing based on operation type
"""

import logging
import random
import time
from typing import List, Dict, Any, Optional, Union
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
from enum import Enum

logger = logging.getLogger(__name__)

class DatabaseRole(Enum):
    """Database role enumeration."""
    PRIMARY = "primary"
    REPLICA = "replica"

class QueryType(Enum):
    """Query type enumeration for routing decisions."""
    READ = "read"
    WRITE = "write"
    ANALYTICS = "analytics"
    ADMIN = "admin"

@dataclass
class DatabaseNode:
    """Database node configuration."""
    name: str
    role: DatabaseRole
    connection_string: str
    weight: int = 1
    max_connections: int = 20
    is_active: bool = True
    last_health_check: Optional[datetime] = None
    health_status: str = "unknown"
    response_time_ms: Optional[float] = None
    connection_count: int = 0

class LoadBalancer:
    """Database load balancer with health monitoring and failover."""
    
    def __init__(self, primary_uri: str, replica_uris: List[str] = None):
        """
        Initialize load balancer.
        
        Args:
            primary_uri: Primary database connection URI
            replica_uris: List of replica database connection URIs
        """
        self.primary_uri = primary_uri
        self.replica_uris = replica_uris or []
        
        # Initialize database nodes
        self.nodes: Dict[str, DatabaseNode] = {}
        self._initialize_nodes()
        
        # Connection pools
        self.engines: Dict[str, Any] = {}
        self.session_factories: Dict[str, Any] = {}
        self._initialize_engines()
        
        # Load balancing state
        self.current_replica_index = 0
        self.health_check_interval = 30  # seconds
        self.health_check_thread = None
        self.health_check_running = False
        
        # Statistics
        self.stats = {
            "total_queries": 0,
            "read_queries": 0,
            "write_queries": 0,
            "failed_queries": 0,
            "replica_failovers": 0,
            "primary_failovers": 0
        }
        
        # Start health monitoring
        self._start_health_monitoring()
    
    def _initialize_nodes(self):
        """Initialize database nodes."""
        # Primary node
        self.nodes["primary"] = DatabaseNode(
            name="primary",
            role=DatabaseRole.PRIMARY,
            connection_string=self.primary_uri,
            weight=1,
            max_connections=50
        )
        
        # Replica nodes
        for i, uri in enumerate(self.replica_uris):
            node_name = f"replica_{i+1}"
            self.nodes[node_name] = DatabaseNode(
                name=node_name,
                role=DatabaseRole.REPLICA,
                connection_string=uri,
                weight=1,
                max_connections=30
            )
    
    def _initialize_engines(self):
        """Initialize SQLAlchemy engines for all nodes."""
        for node_name, node in self.nodes.items():
            try:
                engine = create_engine(
                    node.connection_string,
                    pool_size=node.max_connections,
                    max_overflow=node.max_connections * 2,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False
                )
                self.engines[node_name] = engine
                self.session_factories[node_name] = sessionmaker(bind=engine)
                logger.info(f"Initialized engine for {node_name}")
            except Exception as e:
                logger.error(f"Failed to initialize engine for {node_name}: {e}")
                node.is_active = False
    
    def _start_health_monitoring(self):
        """Start background health monitoring."""
        if self.health_check_thread is None or not self.health_check_thread.is_alive():
            self.health_check_running = True
            self.health_check_thread = threading.Thread(
                target=self._health_monitoring_loop,
                daemon=True
            )
            self.health_check_thread.start()
            logger.info("Started database health monitoring")
    
    def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while self.health_check_running:
            try:
                self._check_all_nodes_health()
                time.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                time.sleep(5)
    
    def _check_all_nodes_health(self):
        """Check health of all database nodes."""
        for node_name, node in self.nodes.items():
            try:
                start_time = time.time()
                
                # Test connection with a simple query
                engine = self.engines.get(node_name)
                if engine:
                    with engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    
                    response_time = (time.time() - start_time) * 1000
                    node.response_time_ms = response_time
                    node.health_status = "healthy"
                    node.last_health_check = datetime.utcnow()
                    
                    # Mark as active if it was inactive
                    if not node.is_active:
                        node.is_active = True
                        logger.info(f"Node {node_name} is now healthy")
                
            except Exception as e:
                node.health_status = "unhealthy"
                node.last_health_check = datetime.utcnow()
                
                # Mark as inactive if it was active
                if node.is_active:
                    node.is_active = False
                    logger.warning(f"Node {node_name} is now unhealthy: {e}")
    
    def get_node_for_query(self, query_type: QueryType) -> Optional[str]:
        """
        Get appropriate database node for query type.
        
        Args:
            query_type: Type of query to route
            
        Returns:
            Node name to use for the query
        """
        if query_type in [QueryType.WRITE, QueryType.ADMIN]:
            # Write operations always go to primary
            if self.nodes["primary"].is_active:
                return "primary"
            else:
                logger.error("Primary database is not available for write operation")
                return None
        
        elif query_type == QueryType.READ:
            # Read operations can use replicas
            available_replicas = [
                name for name, node in self.nodes.items()
                if node.role == DatabaseRole.REPLICA and node.is_active
            ]
            
            if available_replicas:
                # Round-robin selection
                node_name = available_replicas[self.current_replica_index % len(available_replicas)]
                self.current_replica_index += 1
                return node_name
            else:
                # Fallback to primary if no replicas available
                if self.nodes["primary"].is_active:
                    logger.warning("No replicas available, using primary for read")
                    return "primary"
                else:
                    logger.error("No database nodes available for read operation")
                    return None
        
        elif query_type == QueryType.ANALYTICS:
            # Analytics queries prefer replicas with lowest load
            available_replicas = [
                (name, node) for name, node in self.nodes.items()
                if node.role == DatabaseRole.REPLICA and node.is_active
            ]
            
            if available_replicas:
                # Select replica with lowest connection count
                best_replica = min(available_replicas, key=lambda x: x[1].connection_count)
                return best_replica[0]
            else:
                # Fallback to primary
                if self.nodes["primary"].is_active:
                    logger.warning("No replicas available for analytics, using primary")
                    return "primary"
                else:
                    logger.error("No database nodes available for analytics")
                    return None
        
        return None
    
    @contextmanager
    def get_session(self, query_type: QueryType = QueryType.READ):
        """
        Get database session with automatic load balancing.
        
        Args:
            query_type: Type of query to route
            
        Yields:
            SQLAlchemy session
        """
        node_name = self.get_node_for_query(query_type)
        if not node_name:
            raise SQLAlchemyError("No available database nodes")
        
        node = self.nodes[node_name]
        session_factory = self.session_factories[node_name]
        
        # Update statistics
        self.stats["total_queries"] += 1
        if query_type == QueryType.READ:
            self.stats["read_queries"] += 1
        elif query_type == QueryType.WRITE:
            self.stats["write_queries"] += 1
        
        # Increment connection count
        node.connection_count += 1
        
        session = None
        try:
            session = session_factory()
            yield session
        except OperationalError as e:
            # Handle connection failures
            logger.error(f"Database operation failed on {node_name}: {e}")
            self.stats["failed_queries"] += 1
            
            # Mark node as unhealthy
            node.is_active = False
            node.health_status = "unhealthy"
            
            # Try to get another session if this was a read operation
            if query_type == QueryType.READ:
                logger.info("Attempting failover for read operation")
                self.stats["replica_failovers"] += 1
                
                # Try other replicas or primary
                for other_node_name, other_node in self.nodes.items():
                    if other_node_name != node_name and other_node.is_active:
                        try:
                            other_session_factory = self.session_factories[other_node_name]
                            session = other_session_factory()
                            yield session
                            return
                        except Exception:
                            continue
                
                # If all else fails, raise the original error
                raise e
            else:
                raise e
        except Exception as e:
            logger.error(f"Unexpected error in database session: {e}")
            self.stats["failed_queries"] += 1
            raise e
        finally:
            if session:
                session.close()
            # Decrement connection count
            node.connection_count = max(0, node.connection_count - 1)
    
    def execute_read_query(self, query: str, params: Dict = None) -> List[Dict]:
        """
        Execute a read query with load balancing.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results
        """
        with self.get_session(QueryType.READ) as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result]
    
    def execute_write_query(self, query: str, params: Dict = None) -> Any:
        """
        Execute a write query on primary database.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query result
        """
        with self.get_session(QueryType.WRITE) as session:
            result = session.execute(text(query), params or {})
            session.commit()
            return result
    
    def execute_analytics_query(self, query: str, params: Dict = None) -> List[Dict]:
        """
        Execute an analytics query with load balancing.
        
        Args:
            query: SQL query string
            params: Query parameters
            
        Returns:
            Query results
        """
        with self.get_session(QueryType.ANALYTICS) as session:
            result = session.execute(text(query), params or {})
            return [dict(row) for row in result]
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get health status of all database nodes.
        
        Returns:
            Health status information
        """
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "nodes": {},
            "statistics": self.stats.copy(),
            "overall_status": "healthy"
        }
        
        active_nodes = 0
        total_nodes = len(self.nodes)
        
        for node_name, node in self.nodes.items():
            node_status = {
                "role": node.role.value,
                "is_active": node.is_active,
                "health_status": node.health_status,
                "connection_count": node.connection_count,
                "response_time_ms": node.response_time_ms,
                "last_health_check": node.last_health_check.isoformat() if node.last_health_check else None
            }
            status["nodes"][node_name] = node_status
            
            if node.is_active:
                active_nodes += 1
        
        # Determine overall status
        if active_nodes == 0:
            status["overall_status"] = "critical"
        elif active_nodes < total_nodes:
            status["overall_status"] = "degraded"
        else:
            status["overall_status"] = "healthy"
        
        return status
    
    def shutdown(self):
        """Shutdown the load balancer and close all connections."""
        self.health_check_running = False
        
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        
        # Close all engines
        for engine in self.engines.values():
            engine.dispose()
        
        logger.info("Load balancer shutdown completed")

# Global load balancer instance
_load_balancer = None

def get_load_balancer() -> LoadBalancer:
    """Get the global load balancer instance."""
    global _load_balancer
    if _load_balancer is None:
        from app.config import settings
        
        # Get database URIs from configuration
        primary_uri = settings.postgres_uri
        
        # In a real implementation, you would get replica URIs from configuration
        # For now, we'll use the same URI for replicas (in production, these would be different)
        replica_uris = [
            primary_uri.replace("postgres://", "postgres://replica1:"),
            primary_uri.replace("postgres://", "postgres://replica2:"),
        ]
        
        _load_balancer = LoadBalancer(primary_uri, replica_uris)
    
    return _load_balancer

def shutdown_load_balancer():
    """Shutdown the global load balancer."""
    global _load_balancer
    if _load_balancer:
        _load_balancer.shutdown()
        _load_balancer = None 