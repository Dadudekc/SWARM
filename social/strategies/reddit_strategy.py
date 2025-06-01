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

from social.strategies.platform_strategy_base import PlatformStrategy
from social.utils.media_validator import MediaValidator
from social.utils.log_config import LogConfig
from social.strategies.reddit.post_handler import PostHandler
from social.strategies.reddit_media import RedditMediaHandler
from social.strategies.reddit.rate_limiting.rate_limiter import rate_limit, RateLimiter
from social.strategies.reddit.login_handler import LoginHandler

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
        """Handle rate limiting"""
        self.memory_updates["last_action"] = "rate_limit"
        self.memory_updates["last_error"] = {
            "error": "Rate limit exceeded",
            "context": "rate_limit",
            "timestamp": datetime.now().isoformat()
        }
        raise Exception("Rate limit exceeded")

    def _handle_retry(self, error: str, context: str) -> None:
        """Handle retry attempts and update history."""
        retry_entry = {
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to retry history
        if "retry_history" not in self.memory_updates:
            self.memory_updates["retry_history"] = []
        self.memory_updates["retry_history"].append(retry_entry)
        
        # Update retry stats - only increment on actual retries
        if "stats" not in self.memory_updates:
            self.memory_updates["stats"] = {}
        if "retries" not in self.memory_updates["stats"]:
            self.memory_updates["stats"]["retries"] = 0
        # Only increment retry count if this is not the first attempt
        if len(self.memory_updates["retry_history"]) > 1:
            self.memory_updates["stats"]["retries"] += 1
            self.stats["retries"] += 1

    def _handle_error(self, error: str, context: str) -> None:
        """Handle errors and update stats."""
        error_entry = {
            "error": error,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        if "stats" not in self.memory_updates:
            self.memory_updates["stats"] = {}
        if "errors" not in self.memory_updates["stats"]:
            self.memory_updates["stats"]["errors"] = 0
        if "errors" not in self.stats:
            self.stats["errors"] = 0
        if context == "post":
            self.stats["posts"] = 0
            self.memory_updates["stats"]["posts"] = 0
        elif context == "login":
            self.stats["login"] = 0
            self.memory_updates["stats"]["login"] = 0
        # Keep last_action as is for post, rate_limit, and login contexts
        if context not in ("post", "rate_limit", "login"):
            self.memory_updates["last_action"] = None
        self.memory_updates["stats"]["errors"] += 1
        self.stats["errors"] += 1
        self.memory_updates["last_error"] = error_entry
        if self.logger:
            self.logger.error(
                message=f"Error in {context}: {error}",
                platform="reddit",
                status="error"
            )

    def retry_operation(self, operation: str, max_retries: int = 3) -> bool:
        """Retry a failed operation with exponential backoff."""
        retry_count = 0
        while retry_count < max_retries:
            retry_count += 1
            delay = self.calculate_retry_delay(retry_count)
            
            # Log retry attempt
            if self.logger:
                self.logger.info(
                    message=f"Retrying {operation} (attempt {retry_count}/{max_retries})",
                    platform="reddit",
                    status="retry"
                )
            
            # Wait before retry
            time.sleep(delay)
            
            # Add to retry history before attempt
            self._handle_retry(f"Retry attempt {retry_count}", operation)
            
            # Attempt operation based on type
            if operation == "login":
                success = self.login()
            elif operation == "post":
                if hasattr(self, 'last_title') and hasattr(self, 'last_content'):
                    success = self.create_post(self.last_title, self.last_content, getattr(self, 'last_media_files', None))
                else:
                    success = False
            else:
                success = False
                
            if success:
                # Clear retry history on success
                self.memory_updates["retry_history"] = []
                return True
                
            # Handle retry failure
            self._handle_retry(f"Retry {retry_count} failed", operation)
            
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

    def post(self, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Post content to Reddit.
        
        Args:
            content: Content to post
            media_files: Optional list of media files to attach
        Returns:
            True if post was successful, False otherwise
        Raises:
            Exception: If rate limit is exceeded
        """
        try:
            # Always set last_action to post at the start
            self.memory_updates["last_action"] = "post"
            
            # Check rate limits
            if not self.rate_limiter.check_rate_limit("post"):
                self._handle_rate_limit()
                return False
            
            # Only call create_post, do not increment posts here (handled in create_post)
            success = self.create_post(content, content, media_files)
            if not success:
                self._handle_error("Post verification failed", "post")
            return success
            
        except Exception as e:
            if "Rate limit exceeded" in str(e):
                self._handle_rate_limit()
            else:
                self._handle_error(str(e), "post")
            return False

    def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post on Reddit, with retry on recoverable errors."""
        max_retries = 2
        attempt = 0
        while attempt <= max_retries:
            try:
                self.last_title = title
                self.last_content = content
                self.last_media_files = media_files
                
                # Check rate limits again in create_post
                if not self.rate_limiter.check_rate_limit("post"):
                    self._handle_rate_limit()
                    return False
                
                if not self.is_logged_in():
                    self._handle_error("Not logged in", "post")
                    return False
                    
                if media_files:
                    is_valid, error = self._validate_media(media_files, is_video=False)
                    if not is_valid:
                        self._handle_error(error, "validate_media")
                        return False
                        
                success = self.post_handler.create_post(title, content, media_files)
                if success:
                    self.memory_updates["stats"]["posts"] += 1
                    self.memory_updates["stats"]["post"] += 1
                    self.stats["posts"] += 1
                    self.stats["post"] += 1
                    self.memory_updates["last_error"] = None
                    return True
                else:
                    self._handle_error("Post verification failed", "post")
                    return False
                    
            except Exception as e:
                # Only increment retry stats on actual retry (not first attempt)
                if attempt < max_retries:
                    if attempt > 0:  # Only increment retry count after first attempt
                        self._handle_retry(str(e), "post")
                    attempt += 1
                    continue
                else:
                    self._handle_error(str(e), "post")
                    return False
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