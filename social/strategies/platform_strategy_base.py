"""
Platform Strategy Base Module

Base class for all social media platform strategies.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple, Type
import time
import traceback
from datetime import datetime
from functools import wraps
import os
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, WebDriverException

from social.utils.social_common import SocialMediaUtils
from social.utils.log_manager import LogManager
from social.constants.platform_constants import (
    DEFAULT_COOLDOWN,
    PLATFORM_RATE_LIMITS
)

logger = logging.getLogger(__name__)

def retry_with_recovery(operation: str, max_retries: int = None):
    """Standalone decorator for retry logic with exponential backoff and error recovery."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            max_retries_eff = max_retries or self.MAX_RETRIES
            start_time = time.time()
            last_error = None
            for attempt in range(max_retries_eff):
                try:
                    result = func(self, *args, **kwargs)
                    self._track_operation_time(operation, start_time)
                    return result
                except Exception as e:
                    last_error = e
                    context = {
                        "attempt": attempt + 1,
                        "max_retries": max_retries_eff,
                        "args": str(args),
                        "kwargs": str(kwargs)
                    }
                    self._log_error_with_trace(operation, e, context)
                    self.utils.take_screenshot(f"{operation}_error_attempt_{attempt + 1}")
                    self.memory_updates["retry_history"].append({
                        "operation": operation,
                        "attempt": attempt + 1,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })
                    if attempt < max_retries_eff - 1:
                        delay = self._calculate_retry_delay(attempt)
                        self.logger.info(
                            f"Retrying {operation} in {delay:.2f}s (attempt {attempt + 1}/{max_retries_eff})"
                        )
                        time.sleep(delay)
                        continue
            self._update_memory(operation, False, last_error)
            return False
        return wrapper
    return decorator

class PlatformStrategy(ABC):
    """Base class for all social media platform strategies."""
    
    # Error recovery configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 2
    MAX_RETRY_DELAY = 30
    
    def __init__(
        self,
        driver,
        config: dict,
        memory_update: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        *,
        log_manager: Optional[Any] = None
    ):
        """Initialize platform strategy with driver, configuration, and optional log_manager.
        
        Args:
            driver: WebDriver instance
            config: Configuration dictionary
            memory_update: Optional memory update dictionary
            agent_id: Optional agent ID
            log_manager: Optional log manager instance
        """
        self.driver = driver
        self.config = config
        self.agent_id = agent_id or "default"
        self.platform = self.__class__.__name__.replace('Strategy', '').lower()
        self.utils = SocialMediaUtils(driver, config)
        self.logger = log_manager if log_manager is not None else LogManager(self.platform)
        
        # Initialize memory tracking
        default_memory_updates = {
            "login_attempts": 0,
            "post_attempts": 0,
            "media_uploads": 0,
            "errors": [],
            "last_action": None,
            "last_error": None,
            "retry_history": [],
            "operation_times": {},
            "stats": {}
        }
        self.memory_updates = {**default_memory_updates, **(memory_update or {})}

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter."""
        delay = min(self.INITIAL_RETRY_DELAY * (2 ** attempt), self.MAX_RETRY_DELAY)
        jitter = delay * 0.1 * (0.5 + time.time() % 1)  # Add 10% jitter
        return delay + jitter

    def _log_error_with_trace(self, action: str, error: Exception, context: Dict[str, Any]) -> None:
        """Log error with full traceback and context."""
        error_data = {
            "action": action,
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory_updates["errors"].append(error_data)
        self.memory_updates["last_error"] = error_data
        
        self.logger.error(f"{action} failed: {error.__class__.__name__}: {str(error)}", error=error)

    def _track_operation_time(self, operation: str, start_time: float) -> None:
        """Track operation execution time."""
        elapsed = time.time() - start_time
        if operation not in self.memory_updates["operation_times"]:
            self.memory_updates["operation_times"][operation] = []
        self.memory_updates["operation_times"][operation].append(elapsed)

    def _update_memory(self, action: str, success: bool, error: Optional[Exception] = None) -> None:
        """Update memory with action results."""
        self.memory_updates["last_action"] = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "success": success
        }
        if error:
            self._log_error_with_trace(action, error, {"success": success})

    def _log_action(self, action: str, status: str, tags: List[str], error: Optional[str] = None) -> None:
        """Log an action with consistent format."""
        if error:
            self.logger.error(f"{action} - {status}: {error}")
        else:
            self.logger.info(f"{action} - {status}")

    @retry_with_recovery("media_upload")
    def _handle_media_upload(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Handle media upload with memory tracking and retry logic."""
        self.memory_updates["media_uploads"] += 1
        return self.utils.upload_media(media_paths, is_video)

    @retry_with_recovery("media_validation")
    def _validate_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Validate media files with memory tracking and retry logic."""
        return self.utils.validate_media(media_paths, is_video)

    def get_memory_updates(self) -> Dict[str, Any]:
        """Get current memory state."""
        return self.memory_updates

    def get_operation_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all tracked operations."""
        stats = {}
        for operation, times in self.memory_updates["operation_times"].items():
            if times:
                stats[operation] = {
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "total_operations": len(times),
                    "success_rate": len([t for t in times if t > 0]) / len(times)
                }
        return stats

    @abstractmethod
    def is_logged_in(self) -> bool:
        """Check if currently logged into the platform."""
        pass

    @abstractmethod
    def login(self) -> bool:
        """Log into the platform."""
        pass

    @abstractmethod
    def post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Post content to the platform."""
        pass

    def create_post(self) -> str:
        """Create a post with retry logic."""
        return retry_with_recovery("create_post")(self._create_post_impl)(self)

    def _create_post_impl(self) -> str:
        """Implementation of post creation."""
        raise NotImplementedError("Subclasses must implement _create_post_impl")

    def _find_element(self, by: str, value: str, timeout: int = 10) -> Optional[WebElement]:
        """Find an element with timeout.
        
        Args:
            by: Selenium locator strategy
            value: Locator value
            timeout: Timeout in seconds
            
        Returns:
            WebElement if found, None if not found
        """
        try:
            return self.driver.find_element(by, value)
        except (TimeoutException, WebDriverException) as e:
            self.logger.error(f"Failed to find element {by}={value}", error=e)
            return None
    
    def _click_element(self, element: WebElement) -> bool:
        """Click an element with error handling.
        
        Args:
            element: WebElement to click
            
        Returns:
            True if click was successful
        """
        try:
            element.click()
            return True
        except WebDriverException as e:
            self.logger.error("Failed to click element", error=e)
            return False
    
    def _send_keys(self, element: WebElement, text: str) -> bool:
        """Send keys to an element with error handling.
        
        Args:
            element: WebElement to send keys to
            text: Text to send
            
        Returns:
            True if send_keys was successful
        """
        try:
            element.send_keys(text)
            return True
        except WebDriverException as e:
            self.logger.error("Failed to send keys", error=e)
            return False 