"""
Social Media Common Utilities

Common utilities for social media operations.
"""

import os
import time
import logging
from typing import List, Optional, Union, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException
)

from .base import BaseUtils

# Configure basic logger
logger = logging.getLogger(__name__)

class SocialConfig:
    """Configuration for social media operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize social media configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.platform = config.get("platform", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.access_token = config.get("access_token", "")
        self.refresh_token = config.get("refresh_token", "")
        self.rate_limit = config.get("rate_limit", 60)  # requests per minute
        self.timeout = config.get("timeout", 30)  # seconds
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.log_level = config.get("log_level", "INFO")
        self.proxy = config.get("proxy", None)
        self.user_agent = config.get("user_agent", None)
        self.verify_ssl = config.get("verify_ssl", True)
        self.debug = config.get("debug", False)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            "platform": self.platform,
            "username": self.username,
            "password": self.password,
            "api_key": self.api_key,
            "api_secret": self.api_secret,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "rate_limit": self.rate_limit,
            "timeout": self.timeout,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "log_level": self.log_level,
            "proxy": self.proxy,
            "user_agent": self.user_agent,
            "verify_ssl": self.verify_ssl,
            "debug": self.debug
        }
        
    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> 'SocialConfig':
        """Create configuration from dictionary.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            SocialConfig instance
        """
        return cls(config)

class SocialMediaUtils(BaseUtils):
    """Common utilities for social media operations."""
    
    def __init__(self, driver, config: dict):
        """Initialize the utilities.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
        """
        super().__init__(config)
        self.driver = driver
        self.timeout = config.get("timeout", 30)
        self.logger = logger
        
    def wait_for_element(
        self,
        by: By,
        value: str,
        timeout: Optional[int] = None
    ) -> Optional[object]:
        """Wait for an element to be present.
        
        Args:
            by: Selenium By locator
            value: Locator value
            timeout: Optional timeout override
            
        Returns:
            WebElement if found, None otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {value}")
            return None
            
    def wait_for_clickable(
        self,
        by: By,
        value: str,
        timeout: Optional[int] = None
    ) -> Optional[object]:
        """Wait for an element to be clickable.
        
        Args:
            by: Selenium By locator
            value: Locator value
            timeout: Optional timeout override
            
        Returns:
            WebElement if found and clickable, None otherwise
        """
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for clickable element: {value}")
            return None
            
    def retry_click(
        self,
        element: object,
        max_retries: int = 3,
        delay: float = 1.0
    ) -> bool:
        """Retry clicking an element with exponential backoff.
        
        Args:
            element: WebElement to click
            max_retries: Maximum number of retry attempts
            delay: Initial delay between retries
            
        Returns:
            True if click successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                # Wait for element to be clickable
                wait = WebDriverWait(self.driver, delay)
                wait.until(EC.element_to_be_clickable(element))
                
                # Try to click
                element.click()
                return True
            except (ElementClickInterceptedException, NoSuchElementException) as e:
                if attempt == max_retries - 1:
                    self.logger.error(f"Failed to click element after {max_retries} attempts: {e}")
                    return False
                time.sleep(delay * (2 ** attempt))
        return False
        
    def handle_login(
        self,
        username: str,
        password: str,
        username_field: str,
        password_field: str,
        login_button: str
    ) -> bool:
        """Handle login process.
        
        Args:
            username: Username to login with
            password: Password to login with
            username_field: Username field locator
            password_field: Password field locator
            login_button: Login button locator
            
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Wait for and fill username
            username_element = self.wait_for_clickable(By.NAME, username_field)
            if not username_element:
                return False
            username_element.clear()
            username_element.send_keys(username)
            
            # Wait for and fill password
            password_element = self.wait_for_clickable(By.NAME, password_field)
            if not password_element:
                return False
            password_element.clear()
            password_element.send_keys(password)
            
            # Click login button
            login_element = self.wait_for_clickable(By.NAME, login_button)
            if not login_element:
                return False
            return self.retry_click(login_element)
            
        except Exception as e:
            self.logger.error(f"Login failed: {e}")
            return False
            
    def post_content(
        self,
        content: str,
        post_button: str,
        content_field: str
    ) -> bool:
        """Post content to social media.
        
        Args:
            content: Content to post
            post_button: Post button locator
            content_field: Content field locator
            
        Returns:
            True if post successful, False otherwise
        """
        try:
            # Wait for and fill content field
            content_element = self.wait_for_clickable(By.NAME, content_field)
            if not content_element:
                return False
            content_element.clear()
            content_element.send_keys(content)
            
            # Click post button
            post_element = self.wait_for_clickable(By.NAME, post_button)
            if not post_element:
                return False
            return self.retry_click(post_element)
            
        except Exception as e:
            self.logger.error(f"Post failed: {e}")
            return False
            
    def verify_post_success(
        self,
        success_indicator: str,
        timeout: Optional[int] = None
    ) -> bool:
        """Verify if post was successful.
        
        Args:
            success_indicator: Success indicator element locator
            timeout: Optional timeout override
            
        Returns:
            True if post verified successful, False otherwise
        """
        try:
            element = self.wait_for_element(By.CLASS_NAME, success_indicator, timeout)
            return element is not None
        except Exception as e:
            self.logger.error(f"Post verification failed: {e}")
            return False
            
    def validate_media(
        self,
        media_paths: List[str],
        max_size: int,
        allowed_types: List[str],
        is_video: bool = False
    ) -> bool:
        """Validate media files.
        
        Args:
            media_paths: List of media file paths
            max_size: Maximum file size in bytes
            allowed_types: List of allowed file extensions
            is_video: Whether files are videos
            
        Returns:
            True if all files valid, False otherwise
        """
        for path in media_paths:
            if not os.path.exists(path):
                self.logger.error(f"Media file not found: {path}")
                return False
                
            file_size = os.path.getsize(path)
            if file_size > max_size:
                self.logger.error(f"Media file too large: {path} ({file_size} > {max_size})")
                return False
                
            ext = os.path.splitext(path)[1].lower()
            if ext not in allowed_types:
                self.logger.error(f"Invalid media type: {path} ({ext} not in {allowed_types})")
                return False
                
        return True
        
    def upload_media(
        self,
        media_paths: List[str],
        upload_button: str,
        file_input: str
    ) -> bool:
        """Upload media files.
        
        Args:
            media_paths: List of media file paths
            upload_button: Upload button locator
            file_input: File input element locator
            
        Returns:
            True if upload successful, False otherwise
        """
        try:
            # Click upload button
            upload_element = self.wait_for_clickable(By.NAME, upload_button)
            if not upload_element:
                return False
            if not self.retry_click(upload_element):
                return False
                
            # Find file input
            file_input_element = self.wait_for_element(By.NAME, file_input)
            if not file_input_element:
                return False
                
            # Upload each file
            for path in media_paths:
                file_input_element.send_keys(os.path.abspath(path))
                
            return True
            
        except Exception as e:
            self.logger.error(f"Media upload failed: {e}")
            return False 
