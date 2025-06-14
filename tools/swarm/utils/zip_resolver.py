from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List, Set
import requests
from requests.exceptions import RequestException
import time
import json
from datetime import datetime, timedelta

from .zip_cache import ZipCache, CacheConfig
from .rate_limiter import RateLimiter, RateLimitConfig

@dataclass
class ZipResolverConfig:
    """Configuration for ZIP code resolution service."""
    api_url: str
    api_key: str
    cache_config: CacheConfig
    rate_limit_config: RateLimitConfig
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    batch_size: int = 100

class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, threshold: int, timeout: int):
        """Initialize circuit breaker.
        
        Args:
            threshold: Number of failures before opening circuit
            timeout: Time in seconds before attempting to close circuit
        """
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure = 0
        self.is_open = False
        
    def record_failure(self) -> None:
        """Record a failure and potentially open the circuit."""
        self.failures += 1
        self.last_failure = time.time()
        if self.failures >= self.threshold:
            self.is_open = True
            
    def record_success(self) -> None:
        """Record a success and reset failure count."""
        self.failures = 0
        self.is_open = False
        
    def can_execute(self) -> bool:
        """Check if operation can be executed.
        
        Returns:
            bool: True if circuit is closed or timeout has passed
        """
        if not self.is_open:
            return True
            
        # Check if timeout has passed
        if time.time() - self.last_failure >= self.timeout:
            self.is_open = False
            self.failures = 0
            return True
            
        return False

class ZipResolver:
    """Service for resolving ZIP codes with caching and rate limiting."""
    
    def __init__(self, config: ZipResolverConfig):
        """Initialize ZIP resolver with configuration.
        
        Args:
            config: Service configuration
        """
        self.config = config
        self.cache = ZipCache(config.cache_config)
        self.rate_limiter = RateLimiter(config.rate_limit_config)
        self.circuit_breaker = CircuitBreaker(
            config.circuit_breaker_threshold,
            config.circuit_breaker_timeout
        )
        
    def resolve(self, zip_code: str, ip: str) -> Tuple[bool, Dict]:
        """Resolve a ZIP code with caching and rate limiting.
        
        Args:
            zip_code: ZIP code to resolve
            ip: IP address of the requestor
            
        Returns:
            Tuple[bool, Dict]: (is_valid, data) for the ZIP code
        """
        # Check rate limit
        allowed, rate_meta = self.rate_limiter.allow_request(ip)
        if not allowed:
            return False, {'error': 'Rate limit exceeded', **rate_meta}
            
        # Check cache first
        cached = self.cache.get(zip_code)
        if cached is not None:
            return cached
            
        # Check circuit breaker
        if not self.circuit_breaker.can_execute():
            return False, {'error': 'Circuit breaker open'}
            
        # Try to resolve with retries
        for attempt in range(self.config.max_retries):
            try:
                # Call external API
                response = requests.get(
                    self.config.api_url,
                    params={'zip': zip_code},
                    headers={'Authorization': f'Bearer {self.config.api_key}'}
                )
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                is_valid = data.get('valid', False)
                
                # Cache result
                self.cache.set(zip_code, is_valid, data)
                
                # Record success
                self.circuit_breaker.record_success()
                
                return is_valid, data
                
            except RequestException as e:
                print(f"API error resolving ZIP code {zip_code} (attempt {attempt + 1}): {e}")
                
                # Record failure
                self.circuit_breaker.record_failure()
                
                # Wait before retry
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))
                    
        return False, {'error': 'API error after retries'}
        
    def resolve_batch(self, zip_codes: List[str], ip: str) -> Dict[str, Tuple[bool, Dict]]:
        """Resolve multiple ZIP codes in batch.
        
        Args:
            zip_codes: List of ZIP codes to resolve
            ip: IP address of the requestor
            
        Returns:
            Dict[str, Tuple[bool, Dict]]: Mapping of ZIP codes to their results
        """
        results = {}
        
        # Process in batches
        for i in range(0, len(zip_codes), self.config.batch_size):
            batch = zip_codes[i:i + self.config.batch_size]
            
            # Check rate limit for batch
            allowed, rate_meta = self.rate_limiter.allow_request(ip)
            if not allowed:
                for code in batch:
                    results[code] = (False, {'error': 'Rate limit exceeded', **rate_meta})
                continue
                
            # Process each code in batch
            for zip_code in batch:
                results[zip_code] = self.resolve(zip_code, ip)
                
        return results
        
    def get_stats(self) -> Dict:
        """Get service statistics.
        
        Returns:
            Dict containing service stats
        """
        return {
            'cache': self.cache.get_stats(),
            'rate_limiter': self.rate_limiter.get_stats(),
            'circuit_breaker': {
                'is_open': self.circuit_breaker.is_open,
                'failures': self.circuit_breaker.failures,
                'last_failure': self.circuit_breaker.last_failure
            }
        }
        
    def reset(self, zip_code: str, ip: str) -> bool:
        """Reset cache and rate limit for a ZIP code and IP.
        
        Args:
            zip_code: ZIP code to reset
            ip: IP address to reset
            
        Returns:
            bool: True if both resets successful, False otherwise
        """
        cache_reset = self.cache.invalidate(zip_code)
        rate_reset = self.rate_limiter.reset(ip)
        return cache_reset and rate_reset
        
    def warm_cache(self, zip_codes: List[str]) -> None:
        """Warm the cache with a list of ZIP codes.
        
        Args:
            zip_codes: List of ZIP codes to warm cache with
        """
        self.cache.warm_cache(zip_codes)
        
    def get_circuit_breaker_status(self) -> Dict:
        """Get circuit breaker status.
        
        Returns:
            Dict containing circuit breaker status
        """
        return {
            'is_open': self.circuit_breaker.is_open,
            'failures': self.circuit_breaker.failures,
            'last_failure': self.circuit_breaker.last_failure,
            'threshold': self.circuit_breaker.threshold,
            'timeout': self.circuit_breaker.timeout
        } 
