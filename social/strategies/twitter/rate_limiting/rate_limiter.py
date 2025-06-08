"""
Twitter Rate Limiter
------------------
Handles rate limiting for Twitter operations.
"""

import time
from typing import Dict, Optional
from datetime import datetime, timedelta

def rate_limit(operation: str):
    """Decorator for rate limiting operations.
    
    Args:
        operation: Operation type (e.g. 'post', 'login')
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            if not self.rate_limiter.check_rate_limit(operation):
                self._handle_rate_limit()
                return False
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

class RateLimiter:
    """Handles rate limiting for Twitter operations."""
    
    # Rate limits (operations per time window)
    RATE_LIMITS = {
        "post": {"count": 50, "window": 3600},  # 50 posts per hour
        "login": {"count": 5, "window": 300}    # 5 logins per 5 minutes
    }
    
    def __init__(self):
        """Initialize the rate limiter."""
        self.operation_history: Dict[str, list] = {
            "post": [],
            "login": []
        }
        
    def check_rate_limit(self, operation: str) -> bool:
        """Check if an operation is within rate limits.
        
        Args:
            operation: Operation type (e.g. 'post', 'login')
            
        Returns:
            True if operation is allowed, False if rate limit exceeded
        """
        if operation not in self.RATE_LIMITS:
            return True
            
        # Get rate limit config
        limit = self.RATE_LIMITS[operation]
        window = timedelta(seconds=limit["window"])
        
        # Clean old entries
        now = datetime.now()
        self.operation_history[operation] = [
            timestamp for timestamp in self.operation_history[operation]
            if now - timestamp < window
        ]
        
        # Check if limit exceeded
        if len(self.operation_history[operation]) >= limit["count"]:
            return False
            
        # Add current operation
        self.operation_history[operation].append(now)
        return True
        
    def get_remaining_operations(self, operation: str) -> int:
        """Get number of remaining operations in current window.
        
        Args:
            operation: Operation type (e.g. 'post', 'login')
            
        Returns:
            Number of remaining operations
        """
        if operation not in self.RATE_LIMITS:
            return float('inf')
            
        # Get rate limit config
        limit = self.RATE_LIMITS[operation]
        window = timedelta(seconds=limit["window"])
        
        # Clean old entries
        now = datetime.now()
        self.operation_history[operation] = [
            timestamp for timestamp in self.operation_history[operation]
            if now - timestamp < window
        ]
        
        return limit["count"] - len(self.operation_history[operation])
        
    def get_reset_time(self, operation: str) -> Optional[datetime]:
        """Get time when rate limit will reset.
        
        Args:
            operation: Operation type (e.g. 'post', 'login')
            
        Returns:
            Datetime when rate limit will reset, or None if not rate limited
        """
        if operation not in self.RATE_LIMITS:
            return None
            
        # Get rate limit config
        limit = self.RATE_LIMITS[operation]
        window = timedelta(seconds=limit["window"])
        
        # Clean old entries
        now = datetime.now()
        self.operation_history[operation] = [
            timestamp for timestamp in self.operation_history[operation]
            if now - timestamp < window
        ]
        
        if len(self.operation_history[operation]) >= limit["count"]:
            oldest_timestamp = min(self.operation_history[operation])
            return oldest_timestamp + window
            
        return None 
