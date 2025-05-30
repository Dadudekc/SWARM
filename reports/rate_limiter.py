import time
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
import redis
from redis.exceptions import RedisError
import json

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int
    burst_limit: int
    redis_url: str
    window_size: int = 60  # Window size in seconds
    cleanup_interval: int = 300  # Cleanup interval in seconds

class RateLimiter:
    """Rate limiter implementation using Redis for distributed rate limiting."""
    
    def __init__(self, config: RateLimitConfig):
        """Initialize rate limiter with configuration.
        
        Args:
            config: Rate limit configuration
        """
        self.config = config
        self.redis = redis.from_url(config.redis_url)
        self._last_cleanup = time.time()
        
    def allow_request(self, ip: str) -> Tuple[bool, Dict]:
        """Check if a request from an IP should be allowed using sliding window.
        
        Args:
            ip: IP address of the requestor
            
        Returns:
            Tuple[bool, Dict]: (is_allowed, metadata) where metadata contains
                             remaining requests, reset time, etc.
        """
        try:
            now = time.time()
            key = f"ratelimit:{ip}"
            
            # Cleanup old entries periodically
            if now - self._last_cleanup > self.config.cleanup_interval:
                self._cleanup_old_entries()
                self._last_cleanup = now
            
            # Get current window data
            window_data = self._get_window_data(key)
            current_count = len(window_data)
            
            # Check if we're within limits
            if current_count >= self.config.requests_per_minute:
                # Calculate time until next available slot
                oldest_request = min(window_data)
                reset_time = oldest_request + self.config.window_size
                return False, {
                    'error': 'Rate limit exceeded',
                    'reset_time': reset_time,
                    'remaining': 0
                }
            
            # Add current request timestamp
            window_data.append(now)
            
            # Update window data
            self._update_window_data(key, window_data)
            
            # Calculate remaining requests
            remaining = self.config.requests_per_minute - current_count - 1
            
            return True, {
                'remaining': remaining,
                'reset_time': now + self.config.window_size
            }
            
        except RedisError as e:
            print(f"Redis error in rate limiter for IP {ip}: {e}")
            return True, {'error': 'Redis error', 'fallback': True}
            
    def _get_window_data(self, key: str) -> List[float]:
        """Get the current window data for a key.
        
        Args:
            key: Redis key
            
        Returns:
            List[float]: List of timestamps in the current window
        """
        try:
            data = self.redis.get(key)
            if data is None:
                return []
            return json.loads(data)
        except (json.JSONDecodeError, RedisError):
            return []
            
    def _update_window_data(self, key: str, window_data: List[float]) -> None:
        """Update the window data for a key.
        
        Args:
            key: Redis key
            window_data: List of timestamps
        """
        try:
            # Remove timestamps outside the window
            now = time.time()
            window_data = [ts for ts in window_data if now - ts <= self.config.window_size]
            
            # Store updated data
            self.redis.set(key, json.dumps(window_data), ex=self.config.window_size * 2)
        except RedisError as e:
            print(f"Redis error updating window data: {e}")
            
    def _cleanup_old_entries(self) -> None:
        """Clean up old rate limit entries."""
        try:
            pattern = "ratelimit:*"
            keys = self.redis.keys(pattern)
            
            for key in keys:
                window_data = self._get_window_data(key)
                if not window_data:  # Empty window
                    self.redis.delete(key)
                else:
                    # Update window data to remove old entries
                    self._update_window_data(key, window_data)
        except RedisError as e:
            print(f"Redis error during cleanup: {e}")
            
    def reset(self, ip: str) -> bool:
        """Reset rate limit counter for an IP.
        
        Args:
            ip: IP address to reset
            
        Returns:
            bool: True if reset successful, False otherwise
        """
        try:
            key = f"ratelimit:{ip}"
            return bool(self.redis.delete(key))
        except RedisError as e:
            print(f"Redis error resetting rate limit for IP {ip}: {e}")
            return False
            
    def get_stats(self) -> Dict:
        """Get Redis statistics and rate limit metrics.
        
        Returns:
            Dict containing Redis stats and rate limit metrics
        """
        try:
            redis_stats = self.redis.info()
            
            # Get rate limit specific stats
            pattern = "ratelimit:*"
            keys = self.redis.keys(pattern)
            total_requests = sum(len(self._get_window_data(key)) for key in keys)
            
            return {
                'redis': redis_stats,
                'rate_limits': {
                    'total_ips': len(keys),
                    'total_requests': total_requests,
                    'window_size': self.config.window_size,
                    'requests_per_minute': self.config.requests_per_minute,
                    'burst_limit': self.config.burst_limit
                }
            }
        except RedisError as e:
            print(f"Redis error getting stats: {e}")
            return {}
            
    def get_ip_stats(self, ip: str) -> Dict:
        """Get rate limit statistics for a specific IP.
        
        Args:
            ip: IP address to get stats for
            
        Returns:
            Dict containing IP-specific rate limit stats
        """
        try:
            key = f"ratelimit:{ip}"
            window_data = self._get_window_data(key)
            now = time.time()
            
            # Calculate metrics
            current_count = len(window_data)
            oldest_request = min(window_data) if window_data else now
            reset_time = oldest_request + self.config.window_size
            
            return {
                'current_count': current_count,
                'remaining': max(0, self.config.requests_per_minute - current_count),
                'reset_time': reset_time,
                'window_size': self.config.window_size,
                'is_limited': current_count >= self.config.requests_per_minute
            }
        except RedisError as e:
            print(f"Redis error getting IP stats for {ip}: {e}")
            return {} 