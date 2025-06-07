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

from dreamos.social.utils.social_common import SocialMediaUtils
from dreamos.core.log_manager import LogManager
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
        """Initialize the platform strategy.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
            memory_update: Optional memory update dictionary
            agent_id: Optional agent ID
            log_manager: Optional log manager instance
        """
        self.driver = driver
        self.config = config
        self.memory_updates = memory_update or {}
        self.agent_id = agent_id
        self.logger = log_manager
        
        # Initialize with config validation
        self.initialize(config)
        
        self.platform = self.__class__.__name__.replace('Strategy', '').lower()
        self.utils = SocialMediaUtils(driver, config)
        
        # Initialize memory tracking
        self.memory_updates = {
            "stats": {
                "posts": 0,
                "comments": 0,
                "media_uploads": 0,
                "login_attempts": 0
            },
            "last_action": None,
            "last_error": None,
            "retry_history": []
        }
        if memory_update:
            self.memory_updates.update(memory_update)

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
    def _handle_media_upload(self, media_paths: List[str]) -> bool:
        """Handle media upload process.
        
        Args:
            media_paths: List of paths to media files
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            if not media_paths:
                self.memory_updates["last_error"] = {
                    "error": "No media files provided",
                    "context": "media_upload",
                    "timestamp": datetime.now().isoformat()
                }
                return False
                
            # Increment media upload count
            self.memory_updates["stats"]["media_uploads"] += 1
            self.memory_updates["last_action"] = "media_upload"
            
            # Validate media files
            for path in media_paths:
                if not self._validate_media(path):
                    return False
                    
            # Upload media
            for path in media_paths:
                if not self._upload_media(path):
                    self.memory_updates["last_error"] = {
                        "error": f"Failed to upload media: {path}",
                        "context": "media_upload",
                        "timestamp": datetime.now().isoformat()
                    }
                    return False
                    
            return True
            
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "media_upload",
                "timestamp": datetime.now().isoformat()
            }
            return False

    def _validate_media(self, media_path: str) -> bool:
        """Validate a media file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            if not os.path.exists(media_path):
                self.memory_updates["last_error"] = {
                    "error": f"File not found: {media_path}",
                    "context": "media_validation",
                    "timestamp": datetime.now().isoformat()
                }
                return False
                
            # Check file size
            file_size = os.path.getsize(media_path)
            if file_size > self.config.get("max_file_size", 10 * 1024 * 1024):  # Default 10MB
                self.memory_updates["last_error"] = {
                    "error": f"File too large: {media_path}",
                    "context": "media_validation",
                    "timestamp": datetime.now().isoformat()
                }
                return False
                
            # Check file extension
            _, ext = os.path.splitext(media_path)
            allowed_extensions = self.config.get("allowed_extensions", [".jpg", ".jpeg", ".png", ".gif"])
            if ext.lower() not in allowed_extensions:
                self.memory_updates["last_error"] = {
                    "error": f"Unsupported file format: {ext}",
                    "context": "media_validation",
                    "timestamp": datetime.now().isoformat()
                }
                return False
                
            return True
            
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "media_validation",
                "timestamp": datetime.now().isoformat()
            }
            return False

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

    def post(self, content: str, media_paths: Optional[List[str]] = None) -> bool:
        """Create a post with optional media.
        
        Args:
            content: Text content of the post
            media_paths: Optional list of paths to media files
            
        Returns:
            bool: True if post successful, False otherwise
        """
        try:
            if not self.is_logged_in():
                self.memory_updates["last_error"] = {
                    "error": "Not logged in",
                    "context": "post",
                    "timestamp": datetime.now().isoformat()
                }
                return False
                
            # Handle media upload if provided
            if media_paths:
                if not self._handle_media_upload(media_paths):
                    return False
                    
            # Create post
            try:
                success = self.utils.create_post(content)
                if not success:
                    self.memory_updates["last_error"] = {
                        "error": "Failed to create post",
                        "context": "post",
                        "timestamp": datetime.now().isoformat()
                    }
                    return False
                    
                # Update stats
                self.memory_updates["stats"]["posts"] += 1
                self.memory_updates["last_action"] = "post"
                return True
                
            except Exception as e:
                if "button not found" in str(e).lower():
                    self.memory_updates["last_error"] = {
                        "error": "Post button not found",
                        "context": "post",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    self.memory_updates["last_error"] = {
                        "error": str(e),
                        "context": "post",
                        "timestamp": datetime.now().isoformat()
                    }
                return False
                
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "post",
                "timestamp": datetime.now().isoformat()
            }
            return False

    def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post with retry logic.
        
        Args:
            title: Post title
            content: Post content
            media_files: Optional list of media file paths
            
        Returns:
            True if post was created successfully, False otherwise
        """
        return retry_with_recovery("create_post")(self._create_post_impl)(self, title, content, media_files)

    def _create_post_impl(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
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

    def initialize(self, config: dict) -> None:
        """Initialize the strategy with configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValueError: If required configuration keys are missing
        """
        # Validate browser configuration
        if 'browser' not in config:
            raise ValueError("Missing required browser configuration")
            
        browser_config = config['browser']
        required_browser_keys = ['headless', 'window_title', 'window_coords', 'cookies_path']
        missing_keys = [key for key in required_browser_keys if key not in browser_config]
        if missing_keys:
            raise ValueError(f"Missing required browser configuration keys: {', '.join(missing_keys)}")
            
        # Validate window coordinates
        window_coords = browser_config['window_coords']
        required_coords = ['x', 'y', 'width', 'height']
        missing_coords = [coord for coord in required_coords if coord not in window_coords]
        if missing_coords:
            raise ValueError(f"Missing required window coordinates: {', '.join(missing_coords)}")
            
        self.config = config 