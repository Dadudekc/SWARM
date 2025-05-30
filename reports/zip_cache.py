from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List, Set
import redis
from redis.exceptions import RedisError
import json
import time
from datetime import datetime, timedelta

@dataclass
class CacheConfig:
    """Configuration for ZIP code caching."""
    ttl_valid: int = 86400  # 24 hours for valid codes
    ttl_invalid: int = 3600  # 1 hour for invalid codes
    max_size: int = 100000  # Maximum number of cached entries
    redis_url: str = "redis://localhost:6379/0"
    prefetch_threshold: int = 1000  # Number of requests before prefetching
    prefetch_size: int = 100  # Number of entries to prefetch
    cleanup_interval: int = 3600  # Cleanup interval in seconds

class ZipCache:
    """Cache for ZIP code resolution results using Redis."""
    
    def __init__(self, config: CacheConfig):
        """Initialize ZIP cache with configuration.
        
        Args:
            config: Cache configuration
        """
        self.config = config
        self.redis = redis.from_url(config.redis_url)
        self._last_cleanup = time.time()
        self._request_counts = {}  # Track request counts for prefetching
        
    def get(self, zip_code: str) -> Optional[Tuple[bool, Dict]]:
        """Get cached result for a ZIP code.
        
        Args:
            zip_code: ZIP code to look up
            
        Returns:
            Optional[Tuple[bool, Dict]]: Tuple of (is_valid, data) if found, None if not found
        """
        try:
            key = f"zip:{zip_code}"
            data = self.redis.get(key)
            
            # Update request count for prefetching
            self._update_request_count(zip_code)
            
            if data is None:
                return None
                
            # Parse stored data
            is_valid, result = json.loads(data)
            return is_valid, result
            
        except RedisError as e:
            print(f"Redis error getting ZIP code {zip_code}: {e}")
            return None
            
    def set(self, zip_code: str, data: Dict, is_valid: bool) -> bool:
        """Cache a ZIP code resolution result.
        
        Args:
            zip_code: ZIP code to cache
            data: Resolution data to cache
            is_valid: Whether the ZIP code is valid
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"zip:{zip_code}"
            ttl = self.config.ttl_valid if is_valid else self.config.ttl_invalid
            
            # Check cache size
            if self.redis.dbsize() >= self.config.max_size:
                # Remove oldest entries if at capacity
                self._evict_oldest()
                
            # Store data with metadata
            value = json.dumps((is_valid, data))
            return bool(self.redis.set(key, value, ex=ttl))
            
        except RedisError as e:
            print(f"Redis error setting ZIP code {zip_code}: {e}")
            return False
            
    def invalidate(self, zip_code: str) -> bool:
        """Remove a ZIP code from cache.
        
        Args:
            zip_code: ZIP code to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = f"zip:{zip_code}"
            return bool(self.redis.delete(key))
        except RedisError as e:
            print(f"Redis error invalidating ZIP code {zip_code}: {e}")
            return False
            
    def get_stats(self) -> Dict:
        """Get detailed cache statistics.
        
        Returns:
            Dict containing cache stats
        """
        try:
            redis_info = self.redis.info()
            keys = self.redis.keys("zip:*")
            
            # Calculate hit/miss ratios
            hits = redis_info.get('keyspace_hits', 0)
            misses = redis_info.get('keyspace_misses', 0)
            total = hits + misses
            hit_ratio = hits / total if total > 0 else 0
            
            # Get memory usage
            memory_used = redis_info.get('used_memory', 0)
            memory_peak = redis_info.get('used_memory_peak', 0)
            
            # Get prefetch stats
            prefetch_candidates = len([k for k, v in self._request_counts.items() 
                                    if v >= self.config.prefetch_threshold])
            
            return {
                'size': len(keys),
                'memory': {
                    'used': memory_used,
                    'peak': memory_peak
                },
                'performance': {
                    'hits': hits,
                    'misses': misses,
                    'hit_ratio': hit_ratio
                },
                'prefetch': {
                    'candidates': prefetch_candidates,
                    'threshold': self.config.prefetch_threshold
                },
                'ttl': {
                    'valid': self.config.ttl_valid,
                    'invalid': self.config.ttl_invalid
                }
            }
        except RedisError as e:
            print(f"Redis error getting cache stats: {e}")
            return {}
            
    def _evict_oldest(self) -> None:
        """Remove oldest entries from cache when at capacity."""
        try:
            # Get all keys
            keys = self.redis.keys("zip:*")
            
            if not keys:
                return
                
            # Get TTL for each key
            key_ttls = [(key, self.redis.ttl(key)) for key in keys]
            
            # Sort by TTL (ascending)
            key_ttls.sort(key=lambda x: x[1])
            
            # Remove 10% of oldest entries
            num_to_remove = max(1, len(keys) // 10)
            for key, _ in key_ttls[:num_to_remove]:
                self.redis.delete(key)
                
        except RedisError as e:
            print(f"Redis error evicting old entries: {e}")
            
    def _update_request_count(self, zip_code: str) -> None:
        """Update request count for a ZIP code.
        
        Args:
            zip_code: ZIP code to update count for
        """
        self._request_counts[zip_code] = self._request_counts.get(zip_code, 0) + 1
        
        # Check if we should trigger prefetch
        if self._request_counts[zip_code] >= self.config.prefetch_threshold:
            self._prefetch_related(zip_code)
            
    def _prefetch_related(self, zip_code: str) -> None:
        """Prefetch related ZIP codes based on request patterns.
        
        Args:
            zip_code: ZIP code to prefetch related codes for
        """
        try:
            # Generate related ZIP codes (e.g., nearby codes)
            related_codes = self._generate_related_codes(zip_code)
            
            # Prefetch up to prefetch_size codes
            for code in related_codes[:self.config.prefetch_size]:
                if not self.redis.exists(f"zip:{code}"):
                    # Add to prefetch queue
                    self.redis.lpush("prefetch:queue", code)
                    
        except RedisError as e:
            print(f"Redis error during prefetch: {e}")
            
    def _generate_related_codes(self, zip_code: str) -> List[str]:
        """Generate related ZIP codes for prefetching.
        
        Args:
            zip_code: Base ZIP code
            
        Returns:
            List[str]: List of related ZIP codes
        """
        # Simple implementation - generate nearby codes
        # In a real system, this would use geographic data
        try:
            base = int(zip_code)
            return [str(base + i) for i in range(-5, 6) if i != 0]
        except ValueError:
            return []
            
    def _cleanup_old_entries(self) -> None:
        """Remove entries older than the cleanup interval."""
        try:
            current_time = time.time()
            keys = self.redis.keys("zip:*")
            
            for key in keys:
                ttl = self.redis.ttl(key)
                if ttl < 0 or (current_time - self._last_cleanup) > self.config.cleanup_interval:
                    self.redis.delete(key)
            
            self._last_cleanup = current_time
        except RedisError as e:
            print(f"Redis error during cleanup: {e}")
            
    def warm_cache(self, zip_codes: List[str]) -> None:
        """Warm the cache with a list of ZIP codes.
        
        Args:
            zip_codes: List of ZIP codes to warm cache with
        """
        try:
            for zip_code in zip_codes:
                if not self.redis.exists(f"zip:{zip_code}"):
                    self.redis.lpush("warm:queue", zip_code)
        except RedisError as e:
            print(f"Redis error warming cache: {e}") 