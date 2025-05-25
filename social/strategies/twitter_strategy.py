import os
import time
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from .platform_strategy_base import PlatformStrategy
from social.utils.social_common import SocialMediaUtils
from social.utils.log_manager import LogManager, LogLevel
from social.constants.platform_constants import (
    MAX_RETRIES,
    RETRY_DELAY,
    TWITTER_MAX_IMAGES,
    TWITTER_MAX_VIDEO_SIZE,
    TWITTER_SUPPORTED_IMAGE_FORMATS,
    TWITTER_SUPPORTED_VIDEO_FORMATS
)

class TwitterStrategy(PlatformStrategy):
    """Twitter platform strategy with enhanced error handling and memory integration."""
    
    # Twitter-specific constants
    MAX_POST_LENGTH = 280
    LOGIN_URL = "https://twitter.com/login"
    HOME_URL = "https://twitter.com/home"
    COMPOSE_URL = "https://twitter.com/compose/tweet"
    
    def __init__(self, driver, config: dict, memory_update: Optional[Dict[str, Any]] = None):
        """Initialize Twitter strategy with driver and configuration."""
        super().__init__(driver, config, memory_update)
        self.utils = SocialMediaUtils(driver, config, self.platform)
        self.logger = LogManager()
        
        # Initialize memory tracking
        self.memory_updates = {
            "login_attempts": 0,
            "post_attempts": 0,
            "media_uploads": 0,
            "errors": [],
            "last_action": None,
            "last_error": None
        }
    
    def _update_memory(self, action: str, success: bool, error: Optional[Exception] = None) -> None:
        """Update memory with action results."""
        self.memory_updates["last_action"] = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "success": success
        }
        if error:
            self.memory_updates["errors"].append({
                "action": action,
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            })
            self.memory_updates["last_error"] = {
                "action": action,
                "error": str(error),
                "timestamp": datetime.now().isoformat()
            }
    
    def is_logged_in(self) -> bool:
        """Check if user is logged into Twitter."""
        try:
            # Check for login form
            login_form = self.utils.wait_for_element(
                By.XPATH,
                "//form[@action='/sessions']",
                timeout=5
            )
            if login_form:
                self.logger.write_log(
                    platform=self.platform,
                    status="not_logged_in",
                    tags=["login_check"],
                    level=LogLevel.INFO
                )
                return False
            
            # Check for home timeline
            timeline = self.utils.wait_for_element(
                By.XPATH,
                "//div[@data-testid='primaryColumn']",
                timeout=5
            )
            if timeline:
                self.logger.write_log(
                    platform=self.platform,
                    status="logged_in",
                    tags=["login_check"],
                    level=LogLevel.INFO
                )
                return True
            
            return False
            
        except Exception as e:
            self.logger.write_log(
                platform=self.platform,
                status="error",
                tags=["login_check"],
                error=str(e),
                level=LogLevel.ERROR
            )
            self._update_memory("check_login", False, e)
            return False
    
    def login(self) -> bool:
        """Log in to Twitter with credentials from config."""
        for attempt in range(MAX_RETRIES):
            try:
                if not self.config.get("twitter_email") or not self.config.get("twitter_password"):
                    self.logger.write_log(
                        platform=self.platform,
                        status="error",
                        tags=["login"],
                        error="Missing credentials",
                        level=LogLevel.ERROR
                    )
                    self._update_memory("login", False, ValueError("Missing credentials"))
                    return False
                
                # Navigate to login page
                self.driver.get(self.LOGIN_URL)
                time.sleep(2)  # Wait for page load
                
                # Enter email
                email_input = self.utils.wait_for_clickable(
                    By.XPATH,
                    "//input[@autocomplete='username']"
                )
                if not email_input:
                    raise TimeoutException("Email input not found")
                email_input.send_keys(self.config["twitter_email"])
                email_input.send_keys(Keys.RETURN)
                
                # Enter password
                password_input = self.utils.wait_for_clickable(
                    By.XPATH,
                    "//input[@name='password']"
                )
                if not password_input:
                    raise TimeoutException("Password input not found")
                password_input.send_keys(self.config["twitter_password"])
                
                # Click login button
                login_button = self.utils.wait_for_clickable(
                    By.XPATH,
                    "//div[@role='button']//span[text()='Log in']"
                )
                if not login_button or not self.utils.retry_click(login_button):
                    raise ElementClickInterceptedException("Failed to click login button")
                
                # Wait for login to complete
                time.sleep(5)
                
                # Verify login success
                if self.is_logged_in():
                    self.logger.write_log(
                        platform=self.platform,
                        status="success",
                        tags=["login"],
                        level=LogLevel.INFO
                    )
                    self._update_memory("login", True)
                    return True
                else:
                    raise WebDriverException("Login verification failed")
                
            except Exception as e:
                self.logger.write_log(
                    platform=self.platform,
                    status="error",
                    tags=["login"],
                    error=str(e),
                    level=LogLevel.ERROR
                )
                self._update_memory("login", False, e)
                self.utils.take_screenshot("login_error")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return False
        
        return False
    
    def post(
        self,
        content: str,
        media_files: Optional[List[str]] = None
    ) -> bool:
        """Post content to Twitter with optional media."""
        try:
            if not self.is_logged_in():
                if not self.login():
                    raise WebDriverException("Not logged in and login failed")
            
            # Navigate to compose page
            self.driver.get(self.COMPOSE_URL)
            time.sleep(2)
            
            # Format content
            formatted_content = self.utils.format_post_content(content, self.MAX_POST_LENGTH)
            
            # Enter post content
            post_box = self.utils.wait_for_clickable(
                By.XPATH,
                "//div[@data-testid='tweetTextarea_0']"
            )
            if not post_box:
                raise TimeoutException("Post box not found")
            post_box.send_keys(formatted_content)
            
            # Handle media upload if provided
            if media_files:
                if not self.utils.validate_media(media_files):
                    raise ValueError("Invalid media files")
                if not self.utils.upload_media(media_files):
                    raise WebDriverException("Media upload failed")
                self.memory_updates["media_uploads"] += 1
            
            # Click post button
            post_button = self.utils.wait_for_clickable(
                By.XPATH,
                "//div[@data-testid='tweetButton']"
            )
            if not post_button or not self.utils.retry_click(post_button):
                raise ElementClickInterceptedException("Failed to click post button")
            
            # Verify post success
            time.sleep(3)
            if self.utils.verify_post_success(self.HOME_URL):
                self.logger.write_log(
                    platform=self.platform,
                    status="success",
                    tags=["post"],
                    metadata={"content_length": len(formatted_content)},
                    level=LogLevel.INFO
                )
                self._update_memory("post", True)
                self.memory_updates["post_attempts"] += 1
                return True
            else:
                raise WebDriverException("Post verification failed")
            
        except Exception as e:
            self.logger.write_log(
                platform=self.platform,
                status="error",
                tags=["post"],
                error=str(e),
                level=LogLevel.ERROR
            )
            self._update_memory("post", False, e)
            self.utils.take_screenshot("post_error")
            return False
    
    def get_memory_updates(self) -> Dict[str, Any]:
        """Get current memory state."""
        return self.memory_updates 