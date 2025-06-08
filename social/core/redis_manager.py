"""
Redis Manager Module
-----------------
Provides functionality for managing Redis connections and operations.
"""

import redis
from typing import Optional, Any, Dict
from contextlib import contextmanager

class RedisManager:
    """Manager for Redis connections and operations."""
    
    _instance = None
    _connection = None
    
    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Redis manager."""
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._connection = None
            self._config = {
                'host': 'localhost',
                'port': 6379,
                'db': 0,
                'decode_responses': True
            }
    
    def configure(self, **kwargs):
        """Configure Redis connection parameters.
        
        Args:
            **kwargs: Redis connection parameters
        """
        self._config.update(kwargs)
        if self._connection:
            self._connection.close()
            self._connection = None
    
    @classmethod
    def get_connection(cls) -> Optional[redis.Redis]:
        """Get Redis connection.
        
        Returns:
            Redis connection instance or None if not configured
        """
        if cls._connection is None:
            instance = cls()
            try:
                cls._connection = redis.Redis(**instance._config)
                # Test connection
                cls._connection.ping()
            except redis.ConnectionError as e:
                print(f"Failed to connect to Redis: {e}")
                return None
        return cls._connection
    
    @contextmanager
    def get_connection_context(self):
        """Get Redis connection context.
        
        Yields:
            Redis connection instance
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            pass  # Don't close connection as it's shared
    
    def set(self, key: str, value: Any, **kwargs) -> bool:
        """Set a key-value pair in Redis.
        
        Args:
            key: Key to set
            value: Value to set
            **kwargs: Additional Redis SET options
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection_context() as conn:
                if conn:
                    return conn.set(key, value, **kwargs)
            return False
        except Exception as e:
            print(f"Error setting Redis key: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis.
        
        Args:
            key: Key to get
            
        Returns:
            Value if found, None otherwise
        """
        try:
            with self.get_connection_context() as conn:
                if conn:
                    return conn.get(key)
            return None
        except Exception as e:
            print(f"Error getting Redis key: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """Delete a key from Redis.
        
        Args:
            key: Key to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection_context() as conn:
                if conn:
                    return bool(conn.delete(key))
            return False
        except Exception as e:
            print(f"Error deleting Redis key: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis.
        
        Args:
            key: Key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            with self.get_connection_context() as conn:
                if conn:
                    return bool(conn.exists(key))
            return False
        except Exception as e:
            print(f"Error checking Redis key: {e}")
            return False
    
    def close(self):
        """Close Redis connection."""
        if self._connection:
            self._connection.close()
            self._connection = None 
