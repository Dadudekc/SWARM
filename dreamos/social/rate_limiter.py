"""
Rate limiter for social media platforms using token bucket algorithm.
Tracks and enforces posting limits per platform.
"""

import time
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, asdict
import threading

from dreamos.core.utils.logging_utils import get_logger

logger = get_logger(__name__)

@dataclass
class RateLimitConfig:
    """Configuration for platform rate limits."""
    tokens_per_interval: int
    interval_seconds: int
    max_tokens: int = 1

@dataclass
class RateLimitState:
    """Current state of rate limiting."""
    tokens: float
    last_refill: float
    violations: int = 0
    last_violation: Optional[float] = None

class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.max_tokens
        self.last_refill = time.time()
        self.lock = threading.Lock()
        
    def _refill(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_refill
        
        # Calculate tokens to add based on time passed
        tokens_to_add = (time_passed * self.config.tokens_per_interval) / self.config.interval_seconds
        
        # Update tokens and last refill time
        self.tokens = min(self.config.max_tokens, self.tokens + tokens_to_add)
        self.last_refill = now
        
    def acquire(self) -> bool:
        """Try to acquire a token."""
        with self.lock:
            self._refill()
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False
            
    def get_tokens(self) -> float:
        """Get current token count."""
        with self.lock:
            self._refill()
            return self.tokens

class RateLimiter:
    """Manages rate limits for multiple social media platforms."""
    
    # Platform-specific rate limits
    PLATFORM_LIMITS = {
        "twitter": RateLimitConfig(tokens_per_interval=1, interval_seconds=300),  # 1 post / 5 min
        "reddit": RateLimitConfig(tokens_per_interval=1, interval_seconds=600),   # 1 post / 10 min
        "discord": RateLimitConfig(tokens_per_interval=2, interval_seconds=60),   # 2 posts / 1 min
        "instagram": RateLimitConfig(tokens_per_interval=1, interval_seconds=300), # 1 post / 5 min
        "linkedin": RateLimitConfig(tokens_per_interval=1, interval_seconds=300),  # 1 post / 5 min
    }
    
    def __init__(self, log_file: str = "social_post_log.json"):
        self.buckets: Dict[str, TokenBucket] = {}
        self.states: Dict[str, RateLimitState] = {}
        self.log_file = Path(log_file)
        self.lock = threading.Lock()
        
        # Initialize buckets and states
        for platform, config in self.PLATFORM_LIMITS.items():
            self.buckets[platform] = TokenBucket(config)
            self.states[platform] = RateLimitState(
                tokens=config.max_tokens,
                last_refill=time.time()
            )
            
        # Load existing state if available
        self._load_state()
        
    def _load_state(self):
        """Load rate limit state from log file."""
        if self.log_file.exists():
            try:
                with open(self.log_file) as f:
                    data = json.load(f)
                    for platform, state in data.get("rate_limits", {}).items():
                        if platform in self.states:
                            # Update both bucket and state
                            self.states[platform] = RateLimitState(**state)
                            self.buckets[platform].tokens = state["tokens"]
                            self.buckets[platform].last_refill = state["last_refill"]
            except Exception as e:
                logger.error("Failed to load rate limit state: %s", e)
                
    def _save_state(self):
        """Save current rate limit state to log file."""
        try:
            # Sync bucket states before saving
            for platform in self.states:
                self.states[platform].tokens = self.buckets[platform].get_tokens()
                self.states[platform].last_refill = self.buckets[platform].last_refill
                
            data = {
                "rate_limits": {
                    platform: asdict(state)
                    for platform, state in self.states.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("Failed to save rate limit state: %s", e)
            
    def can_post(self, platform: str) -> bool:
        """Check if posting is allowed for the platform."""
        if platform not in self.buckets:
            logger.warning("Unknown platform: %s", platform)
            return False  # Don't allow unknown platforms
            
        with self.lock:
            bucket = self.buckets[platform]
            state = self.states[platform]
            
            if bucket.acquire():
                state.violations = 0
                state.last_violation = None
                self._save_state()
                return True
                
            # Record violation
            state.violations += 1
            state.last_violation = time.time()
            self._save_state()
            
            return False
            
    def get_wait_time(self, platform: str) -> float:
        """Get time until next post is allowed."""
        if platform not in self.buckets:
            return 0.0
            
        with self.lock:
            bucket = self.buckets[platform]
            state = self.states[platform]
            
            if bucket.get_tokens() >= 1.0:
                return 0.0
                
            # Calculate time until next token
            time_since_refill = time.time() - state.last_refill
            tokens_per_second = bucket.config.tokens_per_interval / bucket.config.interval_seconds
            time_for_token = (1.0 - bucket.get_tokens()) / tokens_per_second
            
            return max(0.0, time_for_token - time_since_refill)
            
    def get_platform_stats(self, platform: str) -> Dict:
        """Get current stats for a platform."""
        if platform not in self.states:
            return {}
            
        with self.lock:
            state = self.states[platform]
            bucket = self.buckets[platform]
            
            # Ensure stats are current
            current_tokens = bucket.get_tokens()
            
            return {
                "violations": state.violations,
                "last_violation": datetime.fromtimestamp(state.last_violation).isoformat() if state.last_violation else None,
                "wait_time": self.get_wait_time(platform),
                "tokens": current_tokens
            } 