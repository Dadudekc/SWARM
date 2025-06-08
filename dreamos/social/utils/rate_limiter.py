"""
Rate Limiter Module
-----------------
Provides rate limiting functionality for API calls.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading

class RateLimiter:
    """Handles rate limiting for API operations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize rate limiter.
        
        Args:
            config: Optional configuration dictionary
        """
        self.rules = config.get("rules", {}) if config else {}
        self._last_checks = {}
        self._lock = threading.RLock()
    
    def check_rate_limit(self, platform_name: str, operation: str) -> bool:
        """Check if an operation is within rate limits.
        
        Args:
            platform_name: Name of the platform
            operation: Operation type (post, comment, login)
            
        Returns:
            True if operation is allowed, False if rate limited
        """
        if operation not in self.rules:
            return True
            
        # Reset limits if window has passed
        if datetime.now() - self._last_checks.get(operation, datetime.now()) > timedelta(seconds=self.rules[operation]['window']):
            self.reset_limits(operation)
            
        # Check if we have remaining operations
        if self.rules[operation]['remaining'] <= 0:
            return False
            
        # Decrement remaining count
        self.rules[operation]['remaining'] -= 1
        return True
    
    def set_rate_limit(self, operation: str, limit: int, window: int) -> None:
        """Set rate limit for an operation.
        
        Args:
            operation: Operation type (post, comment, login)
            limit: Maximum number of operations allowed
            window: Time window in seconds
        """
        self.rules[operation] = {
            'limit': limit,
            'window': window,
            'remaining': limit
        }
    
    def reset_limits(self, operation: Optional[str] = None) -> None:
        """Reset rate limits.
        
        Args:
            operation: Optional operation to reset. If None, reset all.
        """
        if operation:
            if operation in self.rules:
                self.rules[operation]['remaining'] = self.rules[operation]['limit']
        else:
            for op in self.rules:
                self.rules[op]['remaining'] = self.rules[op]['limit']
        self._last_checks[operation] = datetime.now()
    
    def get_remaining(self, operation: str) -> int:
        """Get remaining operations for an operation type.
        
        Args:
            operation: Operation type
            
        Returns:
            Number of remaining operations
        """
        return self.rules.get(operation, {}).get('remaining', 0) 
