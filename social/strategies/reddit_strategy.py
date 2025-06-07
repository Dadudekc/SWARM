"""
Reddit Strategy Module
--------------------
Provides functionality for interacting with Reddit.
"""

import time
import os
import random
from unittest.mock import Mock
from typing import Optional, Dict, Any, List, Tuple
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException
)
from datetime import datetime
import praw
import logging

from social.strategies.platform_strategy_base import PlatformStrategy
from social.utils.media_validator import MediaValidator
from social.strategies.reddit.post_handler import PostHandler
from social.strategies.reddit.media import RedditMediaHandler
from social.strategies.reddit.rate_limiting.rate_limiter import rate_limit, RateLimiter
from social.strategies.reddit.login_handler import LoginHandler
from dreamos.core.config.config_manager import ConfigManager
from dreamos.core.log_manager import LogConfig, LogLevel
from dreamos.core.monitoring.metrics import LogMetrics

class RedditStrategy(PlatformStrategy):
    """Strategy for interacting with Reddit."""
    
    # Constants
    MAX_IMAGES = 20
    MAX_VIDEOS = 1
    MAX_VIDEO_SIZE = 100 * 1024 * 1024  # 100MB
    INITIAL_RETRY_DELAY = 2
    MAX_RETRY_DELAY = 30
    
    def __init__(
        self,
        driver,
        config: dict,
        memory_update: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        *,
        log_manager: Optional[Any] = None,
        utils: Optional[Any] = None
    ):
        """Initialize the Reddit strategy.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
            memory_update: Optional memory update dictionary
            agent_id: Optional agent ID
            log_manager: Optional log manager instance
            utils: Optional utils instance
        """
        super().__init__(driver, config, memory_update, agent_id, log_manager=log_manager)
        
        # Initialize validators and handlers
        self.media_validator = MediaValidator()
        self.post_handler = PostHandler(driver, config)
        self.media_handler = RedditMediaHandler(driver, utils or self.utils, self.logger)
        self.login_handler = LoginHandler(driver, config, memory_update)
        self.rate_limiter = RateLimiter()
        
        # Set supported formats
        self.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        self.supported_video_formats = [".mp4", ".mov", ".avi"]
        
        # Set max limits
        self.max_images = self.MAX_IMAGES
        self.max_videos = self.MAX_VIDEOS
        self.max_video_size = self.MAX_VIDEO_SIZE
        
        # Get subreddit from config
        self.subreddit = config.get('reddit', {}).get('subreddit', '')
        
        # Initialize stats
        self.stats = {
            "login": 0,
            "post": 0,
            "comment": 0,
            "posts": 0,
            "comments": 0,
            "media_uploads": 0,
            "errors": 0,
            "retries": 0,
            "login_attempts": 0
        }
        
        # Initialize memory updates with all required keys
        self.memory_updates = memory_update or {
            "last_action": None,
            "last_error": None,
            "retry_history": [],
            "stats": {
                "login": 0,
                "post": 0,
                "comment": 0,
                "posts": 0,
                "comments": 0,
                "media_uploads": 0,
                "errors": 0,
                "retries": 0,
                "login_attempts": 0
            }
        }
        
        # Initialize credentials from config
        self.credentials = config.get('reddit', {}).get('credentials', {})
        
        # Ensure memory_updates has all required stats
        if 'stats' not in self.memory_updates:
            self.memory_updates['stats'] = {}
        
        # Copy stats to memory_updates if not present
        for key, value in self.stats.items():
            if key not in self.memory_updates['stats']:
                self.memory_updates['stats'][key] = value
                
        # Ensure retry_history exists
        if 'retry_history' not in self.memory_updates:
            self.memory_updates['retry_history'] = []

        self._validate_config()
        self._setup_rate_limiter()

    def _validate_config(self) -> None:
        """Validate required configuration values."""
        required_keys = {
            'reddit': {
                'username': str,
                'password': str,
                'client_id': str,
                'client_secret': str,
                'user_agent': str
            }
        }
        
        for section, keys in required_keys.items():
            if section not in self.config:
                raise ValueError(f"Missing configuration section: {section}")
            for key, key_type in keys.items():
                if key not in self.config[section]:
                    raise ValueError(f"Missing configuration key: {section}.{key}")
                if not isinstance(self.config[section][key], key_type):
                    raise ValueError(f"Invalid type for {section}.{key}")

    def _setup_rate_limiter(self) -> None:
        """Setup rate limiting for Reddit API."""
        self.rate_limiter = {
            'last_post': 0,
            'last_comment': 0,
            'min_interval': 60  # Minimum seconds between actions
        }

    def _check_rate_limit(self, action_type: str) -> bool:
        """Check if action is allowed by rate limits."""
        current_time = time.time()
        last_action = self.rate_limiter[f'last_{action_type}']
        
        if current_time - last_action < self.rate_limiter['min_interval']:
            return False
            
        self.rate_limiter[f'last_{action_type}'] = current_time
        return True

    def _handle_error(self, error: Exception, action: str) -> None:
        """Handle and log errors."""
        error_msg = str(error)
        logging.error(f"Reddit {action} error: {error_msg}")
        self.memory_updates.update({
            "last_action": action,
            "last_error": {
                "error": error_msg,
                "timestamp": time.time()
            }
        })

    def calculate_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number
            
        Returns:
            Delay in seconds
        """
        # Calculate base delay with exponential backoff
        base_delay = min(self.INITIAL_RETRY_DELAY * (2 ** (attempt - 1)), self.MAX_RETRY_DELAY)
        
        # Add jitter (±10%)
        jitter = random.uniform(-0.1, 0.1)
        delay = base_delay * (1 + jitter)
        
        return delay

    def _validate_media(self, files: List[str], is_video: bool = False) -> Tuple[bool, Optional[str]]:
        """Validate media files based on type and count.
        
        Args:
            files: List of media file paths
            is_video: Whether the files are videos
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not files:
            return True, None
            
        # Check if files exist
        for file in files:
            if not os.path.exists(file):
                return False, f"File not found: {file}"
                
        # Check file count
        max_files = self.max_videos if is_video else self.max_images
        if len(files) > max_files:
            return False, f"Too many files (max: {max_files})"
            
        # Check file formats
        supported_formats = self.supported_video_formats if is_video else self.supported_image_formats
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() not in supported_formats:
                return False, f"Unsupported file format: {file} (supported: {', '.join(supported_formats)})"
                
            # Check file size
            try:
                size = os.path.getsize(file)
                max_size = self.max_video_size if is_video else 20 * 1024 * 1024  # 20MB for images
                if size > max_size:
                    return False, f"File too large: {file} (max: {max_size / (1024 * 1024):.1f}MB)"
            except OSError as e:
                return False, f"Error checking file size: {file} - {str(e)}"
                
        # Edge case: if is_video is True but no video files are provided
        if is_video and not any(ext.lower() in self.supported_video_formats for _, ext in map(os.path.splitext, files)):
            return False, "No video files provided when is_video=True"
            
        # Edge case: if is_video is False but video files are provided
        if not is_video and any(ext.lower() in self.supported_video_formats for _, ext in map(os.path.splitext, files)):
            return False, "Video files provided when is_video=False"
                
        return True, None

    def _upload_media(self, files: List[str], is_video: bool = False) -> bool:
        """Upload media files to Reddit.
        
        Args:
            files: List of media file paths
            is_video: Whether the files are videos
            
        Returns:
            True if upload was successful, False otherwise
        """
        try:
            # Validate files first
            is_valid, error = self._validate_media(files, is_video)
            if not is_valid:
                self.memory_updates["last_error"] = {
                    "error": error,
                    "context": "upload_media",
                    "timestamp": datetime.now().isoformat()
                }
                self.memory_updates["last_action"] = "media_upload"
                self.memory_updates["stats"]["errors"] += 1
                self.stats["errors"] += 1
                return False
                
            # Try to find and click upload button
            try:
                upload_button = self.utils.wait_for_element(
                    self.driver,
                    By.XPATH,
                    "//button[contains(@class, 'upload')] | //input[@type='file']",
                    timeout=10
                )
                if not upload_button:
                    self.memory_updates["last_error"] = {
                        "error": "Media upload button not found",
                        "context": "upload_media",
                        "timestamp": datetime.now().isoformat()
                    }
                    self.memory_updates["last_action"] = "media_upload"
                    self.memory_updates["stats"]["errors"] += 1
                    self.stats["errors"] += 1
                    return False
                    
                # Click button and upload files
                try:
                    upload_button.click()
                    for file in files:
                        upload_button.send_keys(os.path.abspath(file))
                except ElementClickInterceptedException:
                    self.memory_updates["last_error"] = {
                        "error": "Click intercepted",
                        "context": "upload_media",
                        "timestamp": datetime.now().isoformat()
                    }
                    self.memory_updates["last_action"] = "media_upload"
                    self.memory_updates["stats"]["errors"] += 1
                    self.stats["errors"] += 1
                    return False
                
                self.memory_updates["last_action"] = "media_upload"
                self.memory_updates["stats"]["media_uploads"] += 1
                self.stats["media_uploads"] += 1
                return True
                
            except ElementClickInterceptedException:
                self.memory_updates["last_error"] = {
                    "error": "Click intercepted",
                    "context": "upload_media",
                    "timestamp": datetime.now().isoformat()
                }
                self.memory_updates["last_action"] = "media_upload"
                self.memory_updates["stats"]["errors"] += 1
                self.stats["errors"] += 1
                return False
                
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": f"Error uploading media: {str(e)}",
                "context": "upload_media",
                "timestamp": datetime.now().isoformat()
            }
            self.memory_updates["last_action"] = "media_upload"
            self.memory_updates["stats"]["errors"] += 1
            self.stats["errors"] += 1
            return False

    def _create_media_dir(self, path: str) -> bool:
        """Create media directory if it doesn't exist.
        
        Args:
            path: Directory path
            
        Returns:
            True if directory exists or was created successfully
        """
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create media directory: {str(e)}")
            return False

    def _verify_post_success(self) -> bool:
        """Verify that a post was created successfully."""
        try:
            # Wait for success message or post URL
            success_element = self.utils.wait_for_element(
                self.driver,
                By.XPATH,
                "//div[contains(@class, 'success')] | //a[contains(@href, '/comments/')]",
                timeout=10
            )
            if not success_element:
                self.memory_updates["last_error"] = {
                    "error": "Post verification failed",
                    "context": "post",
                    "timestamp": datetime.now().isoformat()
                }
                self.memory_updates["last_action"] = "post"
                return False
            return True
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "post",
                "timestamp": datetime.now().isoformat()
            }
            self.memory_updates["last_action"] = "post"
            return False

    def _handle_rate_limit(self) -> None:
        """Handle rate limit exceeded."""
        self.memory_updates["last_error"] = {
            "error": "Rate limit exceeded",
            "context": "rate_limit"
        }
        self.memory_updates["last_action"] = "rate_limit"
        self.memory_updates["stats"]["errors"] += 1
        self.stats["errors"] += 1
        if self.logger:
            self.logger.error(
                message="Rate limit exceeded",
                platform="reddit",
                status="error"
            )

    def _handle_retry(self, error: str, context: str) -> None:
        """Handle retry attempts."""
        retry_entry = {
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        if "retry_history" not in self.memory_updates:
            self.memory_updates["retry_history"] = []
        self.memory_updates["retry_history"].append(retry_entry)
        self.memory_updates["stats"]["retries"] += 1
        self.stats["retries"] += 1
        if self.logger:
            self.logger.info(
                message=f"Retrying {context}: {error}",
                platform="reddit",
                status="retry"
            )

    def retry_operation(self, operation: str, max_retries: int = 3) -> bool:
        """Retry an operation with exponential backoff.
        
        Args:
            operation: Operation to retry
            max_retries: Maximum number of retries
            
        Returns:
            True if successful, False otherwise
        """
        attempt = 0
        while attempt <= max_retries:
            try:
                # Execute operation
                if operation == "post":
                    if not hasattr(self, 'last_title') or not hasattr(self, 'last_content'):
                        self._handle_error("No previous post to retry", "retry")
                        return False
                    success = self.create_post(self.last_title, self.last_content, getattr(self, 'last_media_files', None))
                elif operation == "login":
                    success = self.login()
                else:
                    self._handle_error(f"Unknown operation: {operation}", "retry")
                    return False
                    
                if success:
                    return True
                    
                # Only increment retry count if operation failed
                if attempt < max_retries:
                    self._handle_retry(f"Operation {operation} failed", operation)
                    attempt += 1
                    time.sleep(self.calculate_retry_delay(attempt))
                    continue
                else:
                    self._handle_error(f"Operation {operation} failed after {max_retries} retries", "retry")
                    return False
                    
            except Exception as e:
                if attempt < max_retries:
                    self._handle_retry(str(e), operation)
                    attempt += 1
                    time.sleep(self.calculate_retry_delay(attempt))
                    continue
                else:
                    self._handle_error(str(e), operation)
                    return False
                    
        return False

    @rate_limit("login")
    def login(self) -> bool:
        """Login to Reddit using credentials from config."""
        # Set last action before any operations
        self.memory_updates["last_action"] = "is_logged_in"
        
        if not self.credentials:
            self._handle_error("Missing credentials", "login")
            return False
            
        # Rest of login logic
        self.driver.get("https://www.reddit.com/login")
        success = self.login_handler.login()
        if success:
            self.memory_updates["last_action"] = "login"
            self.memory_updates["stats"]["login"] += 1
            self.stats["login"] += 1
            self.memory_updates["last_error"] = None
            return True
        self._handle_error("Login failed", "login")
        return False

    def post_devlog(self, title: str, content: str, level: str = "INFO") -> bool:
        """Post a development log entry.
        
        Args:
            title: Title of the log entry
            content: Content of the log entry
            level: Log level (INFO, WARNING, ERROR, etc.)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a formatted log entry
            log_entry = {
                "title": title,
                "content": content,
                "level": level,
                "timestamp": datetime.now().isoformat()
            }
            
            # Write to log file
            if self.logger:
                self.logger.info(f"DevLog: {title} - {content}")
            
            # Create the post
            success = self.create_post(title, content)
            
            if success:
                # Update memory
                self.memory_updates["last_action"] = "post"
                self.memory_updates["stats"]["post"] = self.memory_updates["stats"].get("post", 0) + 1
                self.memory_updates["stats"]["devlogs"] = self.memory_updates["stats"].get("devlogs", 0) + 1
                return True
            else:
                self._handle_error("Failed to create devlog post", "devlog")
                return False
            
        except Exception as e:
            self._handle_error(e, "devlog")
            return False

    def post(self, content: str, media_files: Optional[List[str]] = None, title: Optional[str] = None) -> bool:
        """Post content to Reddit.
        
        Args:
            content: Content to post
            media_files: Optional list of media files to attach
            title: Optional title for the post
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if logged in
            if not self.is_logged_in():
                self._handle_error("Not logged in", "post")
                return False
                
            # Check rate limit
            if not self._check_rate_limit('post'):
                self._handle_rate_limit()
                return False
                
            # Use default title if none provided
            title = title or "New Post"
            
            # Create the post
            success = self.create_post(title, content, media_files)
            
            if success:
                self.memory_updates["last_action"] = "post"
                self.memory_updates["stats"]["posts"] = self.memory_updates["stats"].get("posts", 0) + 1
                return True
            else:
                self._handle_error("Post verification failed", "post")
                return False
                
        except Exception as e:
            self._handle_error(e, "post")
            return False

    def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post on Reddit.
        
        Args:
            title: Post title
            content: Post content
            media_files: Optional list of media files
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate media files if provided
            if media_files:
                is_video = any(ext.lower() in self.supported_video_formats for _, ext in map(os.path.splitext, media_files))
                is_valid, error = self._validate_media(media_files, is_video)
                if not is_valid:
                    self._handle_error(ValueError(error), "post")
                    return False
                    
            # Create post using handler
            success = self.post_handler.create_post(title, content, media_files)
            
            if success:
                # Verify post was created
                if not self._verify_post_success():
                    self._handle_error("Post verification failed", "post")
                    return False
                    
                # Update stats
                self.memory_updates["stats"]["posts"] = self.memory_updates["stats"].get("posts", 0) + 1
                if media_files:
                    self.memory_updates["stats"]["media_uploads"] = self.memory_updates["stats"].get("media_uploads", 0) + 1
                    
                return True
            else:
                self._handle_error("Failed to create post", "post")
                return False
                
        except Exception as e:
            self._handle_error(e, "post")
            return False

    def comment(self, post_url: str, comment_text: str) -> bool:
        """Post a comment on a Reddit post."""
        try:
            if not self.is_logged_in():
                self.memory_updates["last_error"] = {
                    "error": "Message: Network error\n",
                    "context": "comment"
                }
                self.memory_updates["last_action"] = "comment"
                return False
                
            self.driver.get(post_url)
            
            comment_box = self.utils.wait_for_element(By.XPATH, "//div[@role='textbox']")
            if not comment_box:
                self.memory_updates["last_error"] = {
                    "error": "Message: Network error\n",
                    "context": "comment"
                }
                self.memory_updates["last_action"] = "comment"
                return False
                
            comment_box.send_keys(comment_text)
            
            submit_button = self.utils.wait_for_clickable(By.XPATH, "//button[@type='submit']")
            if not submit_button:
                self.memory_updates["last_error"] = {
                    "error": "Submit button not found",
                    "context": "comment"
                }
                self.memory_updates["last_action"] = "comment"
                return False
                
            if not self.utils.retry_click(submit_button):
                self.memory_updates["last_error"] = {
                    "error": "Failed to click submit button",
                    "context": "comment"
                }
                self.memory_updates["last_action"] = "comment"
                return False
                
            self.memory_updates["stats"]["comment"] += 1
            self.memory_updates["last_action"] = "comment"
            self.memory_updates["last_error"] = None
            return True
            
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "comment"
            }
            self.memory_updates["last_action"] = "comment"
            return False

    def is_logged_in(self) -> bool:
        """Check if user is logged in to Reddit.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Set last action first
            self.memory_updates["last_action"] = "is_logged_in"
            
            # Check for login form first
            login_form = self.utils.wait_for_element(
                self.driver,
                By.XPATH,
                "//form[@id='login-form']",
                timeout=2
            )
            if login_form is not None:
                self.memory_updates["last_error"] = {
                    "error": "Login form found, user not logged in",
                    "context": "is_logged_in"
                }
                return False
                
            # Check for user menu
            user_menu = self.utils.wait_for_element(
                self.driver,
                By.XPATH,
                "//button[contains(@class, 'user-menu')] | //a[contains(@href, '/logout')]",
                timeout=2
            )
            if user_menu is None:
                self.memory_updates["last_error"] = {
                    "error": "User menu not found, user not logged in",
                    "context": "is_logged_in"
                }
                return False
            
            self.memory_updates["last_error"] = None
            return True
            
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "is_logged_in"
            }
            return False

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