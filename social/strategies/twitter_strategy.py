"""
Twitter Strategy Module
---------------------
Provides functionality for interacting with Twitter.
"""

import time
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    WebDriverException
)

from .platform_strategy_base import PlatformStrategy
from ..utils.media_validator import MediaValidator
from dreamos.core.log_manager import LogConfig
from ..strategies.twitter.post_handler import PostHandler
from ..strategies.twitter.media_handler import TwitterMediaHandler
from ..strategies.twitter.rate_limiting.rate_limiter import rate_limit, RateLimiter
from ..strategies.twitter.login_handler import LoginHandler

class TwitterStrategy(PlatformStrategy):
    """Strategy for interacting with Twitter."""
    
    # Constants
    MAX_IMAGES = 4
    MAX_VIDEOS = 1
    MAX_VIDEO_SIZE = 512 * 1024 * 1024  # 512MB
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
        """Initialize the Twitter strategy.
        
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
        self.media_handler = TwitterMediaHandler(driver, utils or self.utils, self.logger)
        self.login_handler = LoginHandler(driver, config, memory_update)
        self.rate_limiter = RateLimiter()
        
        # Set supported formats
        self.supported_image_formats = [".jpg", ".jpeg", ".png", ".gif"]
        self.supported_video_formats = [".mp4", ".mov"]
        
        # Set max limits
        self.max_images = self.MAX_IMAGES
        self.max_videos = self.MAX_VIDEOS
        self.max_video_size = self.MAX_VIDEO_SIZE
        
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
        self.credentials = config.get('twitter', {}).get('credentials', {})
        
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

    def _handle_rate_limit(self) -> None:
        """Handle rate limiting"""
        self.memory_updates["last_action"] = "rate_limit"
        self.memory_updates["last_error"] = {
            "error": "Rate limit exceeded",
            "context": "rate_limit",
            "timestamp": datetime.now().isoformat()
        }
        raise Exception("Rate limit exceeded")

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
                platform="twitter",
                status="error"
            )

    @rate_limit("login")
    def login(self) -> bool:
        """Login to Twitter using credentials from config."""
        # Set last action before any operations
        self.memory_updates["last_action"] = "is_logged_in"
        
        if not self.credentials:
            self._handle_error("Missing credentials", "login")
            return False
            
        # Rest of login logic
        self.driver.get("https://twitter.com/login")
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
        """Post content to Twitter.
        
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
        """Create a post on Twitter, with retry on recoverable errors."""
        max_retries = 2
        attempt = 0
        while attempt <= max_retries:
            try:
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

    def is_logged_in(self) -> bool:
        """Check if user is logged in to Twitter.
        
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
            
            # If we get here, we found the user menu and no login form
            self.memory_updates["last_error"] = None
            return True
            
        except Exception as e:
            self.memory_updates["last_error"] = {
                "error": str(e),
                "context": "is_logged_in"
            }
            return False 