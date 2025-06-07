"""
Base Strategy
-----------
Base class for social media strategies.
"""

import os
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from abc import ABC, abstractmethod
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from dreamos.core.log_manager import LogConfig, LogLevel
from dreamos.core.log_manager import LogManager
from dreamos.core.monitoring.metrics import LogMetrics
from social.utils.social_common import SocialMediaUtils
from dreamos.core.agent_control.devlog_manager import DevLogManager
from social.config.social_config import PlatformConfig
from social.driver.proxy_manager import ProxyManager
from dreamos.core.config.config_manager import ConfigManager

class SocialMediaStrategy(ABC):
    """Base class for social media strategies."""
    
    # Constants
    INITIAL_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 60.0  # seconds
    MAX_RETRIES = 3
    
    def __init__(
        self,
        config: Dict[str, Any],
        memory_updates: Dict[str, Any],
        agent_id: str,
        logger: Optional[LogManager] = None
    ):
        """Initialize the strategy.
        
        Args:
            config: Configuration dictionary
            memory_updates: Memory updates dictionary
            agent_id: Agent ID
            logger: Optional logger instance
        """
        self.config = config
        self.memory_updates = memory_updates
        self.agent_id = agent_id
        
        # Initialize logger
        if logger:
            self.logger = logger
        else:
            self.logger = LogManager(
                log_dir=config.get("log_config", {}).get("log_dir", "logs"),
                level=config.get("log_config", {}).get("level", "INFO"),
                output_format=config.get("log_config", {}).get("output_format", "text")
            )
        
        # Initialize utils
        self.utils = SocialMediaUtils(self.logger)
        
        # Initialize handlers
        self.login_handler = None
        self.logout_handler = None
        self.post_handler = None
        self.media_handler = None
        
        # Initialize rate limiter
        self.rate_limiter = None
        
        # Initialize memory
        self._init_memory()
        
        # Initialize metrics
        self._metrics = LogMetrics(self.config)
    
    def _init_memory(self):
        """Initialize memory updates."""
        if "stats" not in self.memory_updates:
            self.memory_updates["stats"] = {}
        if "retry_history" not in self.memory_updates:
            self.memory_updates["retry_history"] = []
    
    def login(self) -> bool:
        """Login to the platform.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            if not self.login_handler:
                raise NotImplementedError("Login handler not implemented")
            
            success = self.login_handler.login()
            if success:
                self._update_memory("login", stats={"login": 1})
            else:
                self._update_memory("login", error="Login failed")
            
            return success
        except Exception as e:
            self._update_memory("login", error=str(e))
            return False
    
    def logout(self) -> bool:
        """Logout from the platform.
        
        Returns:
            bool: True if logout successful, False otherwise
        """
        try:
            if not self.logout_handler:
                raise NotImplementedError("Logout handler not implemented")
            
            success = self.logout_handler.logout()
            if success:
                self._update_memory("logout")
            else:
                self._update_memory("logout", error="Logout failed")
            
            return success
        except Exception as e:
            self._update_memory("logout", error=str(e))
            return False
    
    def post(self, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post.
        
        Args:
            content: Post content
            media_files: Optional list of media files to attach
            
        Returns:
            bool: True if post successful, False otherwise
        """
        try:
            if not self.post_handler:
                raise NotImplementedError("Post handler not implemented")
            
            # Check rate limit
            if self.rate_limiter and self.rate_limiter._is_rate_limited("post"):
                delay = self.rate_limiter.calculate_delay()
                self._update_memory("post", error=f"Rate limit exceeded. Try again in {delay:.1f} seconds")
                return False
            
            # Validate media if provided
            if media_files:
                is_valid, error = self._validate_media(media_files)
                if not is_valid:
                    self._update_memory("post", error=f"Media validation failed: {error}")
                    return False
            
            # Create post
            success = self.post_handler.create_post(content, media_files)
            if success:
                self._update_memory("post", stats={"posts": 1})
                if media_files:
                    self._update_memory("post", stats={"media_uploads": len(media_files)})
            else:
                self._update_memory("post", error="Post creation failed")
            
            return success
        except Exception as e:
            self._update_memory("post", error=str(e))
            return False
    
    def _validate_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files.
        
        Args:
            files: List of file paths
            is_video: Whether files are videos
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            if not self.media_handler:
                raise NotImplementedError("Media handler not implemented")
            
            return self.media_handler.validate_media(files, is_video)
        except Exception as e:
            return False, str(e)
    
    def _upload_media(self, files: List[str]) -> bool:
        """Upload media files.
        
        Args:
            files: List of file paths
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            if not self.media_handler:
                raise NotImplementedError("Media handler not implemented")
            
            success = self.media_handler.upload_media(files)
            if success:
                self._update_memory("upload_media", stats={"media_uploads": len(files)})
            else:
                self._update_memory("upload_media", error="Media upload failed")
            
            return success
        except Exception as e:
            self._update_memory("upload_media", error=str(e))
            return False
    
    def _update_memory(
        self,
        action: str,
        error: Optional[str] = None,
        stats: Optional[Dict[str, int]] = None
    ):
        """Update memory with action and error.
        
        Args:
            action: Action performed
            error: Optional error message
            stats: Optional stats to update
        """
        self.memory_updates["last_action"] = action
        
        if error:
            self.memory_updates["last_error"] = {
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "action": action
            }
            if "errors" not in self.memory_updates["stats"]:
                self.memory_updates["stats"]["errors"] = 0
            self.memory_updates["stats"]["errors"] += 1
        
        if stats:
            for key, value in stats.items():
                if key not in self.memory_updates["stats"]:
                    self.memory_updates["stats"][key] = 0
                self.memory_updates["stats"][key] += value
    
    def calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number
            
        Returns:
            float: Delay in seconds
        """
        import random
        
        # Calculate base delay with exponential backoff
        delay = self.INITIAL_RETRY_DELAY * (2 ** (attempt - 1))
        
        # Add jitter (±10%)
        jitter = random.uniform(-0.1, 0.1)
        delay *= (1 + jitter)
        
        # Cap at max delay
        return min(delay, self.MAX_RETRY_DELAY)
    
    def take_screenshot(self) -> Optional[str]:
        """Take a screenshot.
        
        Returns:
            Optional[str]: Path to screenshot if successful, None otherwise
        """
        try:
            return self.utils.take_screenshot()
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Wait for element to be present.
        
        Args:
            by: Selenium By locator
            value: Locator value
            timeout: Optional timeout in seconds
            
        Returns:
            Optional[Any]: Element if found, None otherwise
        """
        try:
            return self.utils.wait_for_element(by, value, timeout)
        except Exception as e:
            self.logger.error(f"Failed to wait for element: {e}")
            return None
    
    def wait_for_clickable(self, by: By, value: str, timeout: Optional[int] = None) -> Optional[Any]:
        """Wait for element to be clickable.
        
        Args:
            by: Selenium By locator
            value: Locator value
            timeout: Optional timeout in seconds
            
        Returns:
            Optional[Any]: Element if found and clickable, None otherwise
        """
        try:
            return self.utils.wait_for_clickable(by, value, timeout)
        except Exception as e:
            self.logger.error(f"Failed to wait for clickable element: {e}")
            return None
    
    def record_metric(self, metric_type: str, value: float, tags: Optional[List[str]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a metric.
        
        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Optional tags
            metadata: Optional metadata
        """
        self._metrics.record_metric(metric_type, value, tags, metadata)
        
    def get_metrics(self, metric_type: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metrics with optional filtering.
        
        Args:
            metric_type: Optional metric type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            Dictionary of metric entries
        """
        return self._metrics.get_metrics(metric_type, start_time, end_time)
        
    def get_summary(self, metric_type: Optional[str] = None, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict[str, Any]:
        """Get metric summary statistics.
        
        Args:
            metric_type: Optional metric type to filter by
            start_time: Optional start time to filter by
            end_time: Optional end time to filter by
            
        Returns:
            Dictionary of summary statistics
        """
        return self._metrics.get_summary(metric_type, start_time, end_time)
        
    def save_metrics(self, filepath: Optional[str] = None) -> None:
        """Save metrics to file.
        
        Args:
            filepath: Optional file path to save to
        """
        self._metrics.save_metrics(filepath)
        
    def load_metrics(self, filepath: Optional[str] = None) -> None:
        """Load metrics from file.
        
        Args:
            filepath: Optional file path to load from
        """
        self._metrics.load_metrics(filepath)
        
    def clear_metrics(self) -> None:
        """Clear all metrics."""
        self._metrics.clear_metrics() 