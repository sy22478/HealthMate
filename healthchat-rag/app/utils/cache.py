"""
Caching utilities for HealthMate backend.

This module provides:
- Redis-based caching for API responses
- Database query result caching
- Session caching and management
- Cache invalidation strategies
"""

import json
import hashlib
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import pickle
from functools import wraps
import redis
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class CacheManager:
    """Redis-based cache manager for HealthMate."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", default_ttl: int = 3600):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Keep as bytes for pickle compatibility
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        # Create a string representation of arguments
        key_parts = [prefix]
        
        if args:
            key_parts.extend([str(arg) for arg in args])
        
        if kwargs:
            # Sort kwargs for consistent key generation
            sorted_kwargs = sorted(kwargs.items())
            key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
        
        key_string = ":".join(key_parts)
        
        # Create hash for long keys
        if len(key_string) > 250:
            return f"{prefix}:{hashlib.md5(key_string.encode()).hexdigest()}"
        
        return key_string
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            # Serialize value using pickle for complex objects
            serialized_value = pickle.dumps(value)
            
            # Use default TTL if not specified
            cache_ttl = ttl if ttl is not None else self.default_ttl
            
            result = self.redis_client.setex(key, cache_ttl, serialized_value)
            
            logger.debug(f"Cache set: {key} (TTL: {cache_ttl}s)")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set cache key {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            
            if value is None:
                return None
            
            # Deserialize value
            deserialized_value = pickle.loads(value)
            
            logger.debug(f"Cache hit: {key}")
            return deserialized_value
            
        except Exception as e:
            logger.error(f"Failed to get cache key {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to delete cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in cache.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Failed to check cache key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            key: Cache key
            ttl: Time-to-live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            result = self.redis_client.expire(key, ttl)
            logger.debug(f"Cache expire: {key} (TTL: {ttl}s)")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Failed to set expiration for cache key {key}: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "user:*", "health_data:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Failed to clear cache pattern {pattern}: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache statistics
        """
        if not self.redis_client:
            return {"error": "Redis not connected"}
        
        try:
            info = self.redis_client.info()
            
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "uptime": info.get("uptime_in_seconds", 0),
                "db_size": self.redis_client.dbsize()
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}

# Global cache manager instance
cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global cache_manager
    if cache_manager is None:
        from app.config import settings
        redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379')
        cache_manager = CacheManager(redis_url)
    return cache_manager

def cache_result(prefix: str, ttl: Optional[int] = None, key_generator: Optional[callable] = None):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        key_generator: Custom key generation function
        
    Usage:
        @cache_result("user_profile", ttl=1800)
        def get_user_profile(user_id: int):
            # Function implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key
            if key_generator:
                cache_key = key_generator(*args, **kwargs)
            else:
                cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def cache_api_response(prefix: str, ttl: Optional[int] = None):
    """
    Decorator to cache API endpoint responses.
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        
    Usage:
        @cache_api_response("health_data", ttl=300)
        async def get_health_data(user_id: int):
            # API endpoint implementation
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            
            # Generate cache key from function name and arguments
            cache_key = cache._generate_key(f"api:{prefix}", func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern: str):
    """
    Decorator to invalidate cache after function execution.
    
    Args:
        pattern: Cache pattern to invalidate
        
    Usage:
        @invalidate_cache_pattern("user:*")
        def update_user_profile(user_id: int):
            # Function that updates user data
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Invalidate cache after function execution
            cache = get_cache_manager()
            cache.clear_pattern(pattern)
            
            return result
        return wrapper
    return decorator

@contextmanager
def cache_transaction():
    """
    Context manager for cache transactions.
    
    Usage:
        with cache_transaction() as cache:
            cache.set("key1", "value1")
            cache.set("key2", "value2")
            # All operations are atomic
    """
    cache = get_cache_manager()
    try:
        yield cache
    except Exception as e:
        logger.error(f"Cache transaction failed: {e}")
        raise

class SessionCache:
    """Session-specific caching utility."""
    
    def __init__(self, session_id: str, ttl: int = 3600):
        """
        Initialize session cache.
        
        Args:
            session_id: Unique session identifier
            ttl: Session TTL in seconds
        """
        self.session_id = session_id
        self.ttl = ttl
        self.cache = get_cache_manager()
    
    def _get_session_key(self, key: str) -> str:
        """Generate session-specific cache key."""
        return f"session:{self.session_id}:{key}"
    
    def set(self, key: str, value: Any) -> bool:
        """Set session-specific value."""
        session_key = self._get_session_key(key)
        return self.cache.set(session_key, value, self.ttl)
    
    def get(self, key: str) -> Optional[Any]:
        """Get session-specific value."""
        session_key = self._get_session_key(key)
        return self.cache.get(session_key)
    
    def delete(self, key: str) -> bool:
        """Delete session-specific value."""
        session_key = self._get_session_key(key)
        return self.cache.delete(session_key)
    
    def clear(self) -> int:
        """Clear all session data."""
        pattern = f"session:{self.session_id}:*"
        return self.cache.clear_pattern(pattern)

class QueryCache:
    """Database query result caching utility."""
    
    def __init__(self, ttl: int = 300):
        """
        Initialize query cache.
        
        Args:
            ttl: Default TTL for query results
        """
        self.ttl = ttl
        self.cache = get_cache_manager()
    
    def cache_query(self, query: str, params: Optional[Dict] = None, ttl: Optional[int] = None):
        """
        Decorator to cache database query results.
        
        Args:
            query: SQL query string
            params: Query parameters
            ttl: Custom TTL for this query
            
        Usage:
            @query_cache.cache_query("SELECT * FROM users WHERE id = :id")
            def get_user_by_id(user_id: int):
                # Database query implementation
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from query and parameters
                cache_key = self.cache._generate_key("query", query, params or {})
                
                # Try to get from cache
                cached_result = self.cache.get(cache_key)
                if cached_result is not None:
                    return cached_result
                
                # Execute query and cache result
                result = func(*args, **kwargs)
                cache_ttl = ttl if ttl is not None else self.ttl
                self.cache.set(cache_key, result, cache_ttl)
                
                return result
            return wrapper
        return decorator
    
    def invalidate_table(self, table_name: str):
        """
        Decorator to invalidate cache for a specific table.
        
        Args:
            table_name: Name of the table to invalidate
            
        Usage:
            @query_cache.invalidate_table("users")
            def update_user(user_id: int):
                # Function that modifies user data
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                result = func(*args, **kwargs)
                
                # Invalidate all queries related to this table
                pattern = f"query:*{table_name}*"
                self.cache.clear_pattern(pattern)
                
                return result
            return wrapper
        return decorator

# Global query cache instance
query_cache = QueryCache() 