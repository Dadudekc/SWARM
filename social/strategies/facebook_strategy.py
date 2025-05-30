"""
Facebook Strategy Module

Handles Facebook-specific social media operations.
"""

from typing import Optional, Dict, Any, List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException

from .platform_strategy_base import PlatformStrategy
from ..utils.social_common import SocialMediaUtils
from ..utils.log_manager import LogManager
from social.constants.platform_constants import (
    FACEBOOK_MAX_IMAGES,
    FACEBOOK_MAX_VIDEO_SIZE,
    FACEBOOK_SUPPORTED_IMAGE_FORMATS,
    FACEBOOK_SUPPORTED_VIDEO_FORMATS
)

class FacebookStrategy(PlatformStrategy):
    """Enhanced Facebook platform strategy with media support and robust error handling."""
    
    LOGIN_URL = "https://facebook.com/login"
    HOME_URL = "https://facebook.com"
    POST_URL = "https://facebook.com/home"
    
    def __init__(
        self,
        driver,
        config: dict,
        memory_update: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
        *,
        log_manager: Optional[Any] = None
    ):
        """Initialize Facebook strategy with driver, configuration, and optional log_manager.
        
        Args:
            driver: WebDriver instance
            config: Configuration dictionary
            memory_update: Optional memory update dictionary
            agent_id: Optional agent ID
            log_manager: Optional log manager instance
        """
        super().__init__(
            driver=driver,
            config=config,
            memory_update=memory_update,
            agent_id=agent_id,
            log_manager=log_manager
        )
        
        # Set platform-specific constants
        self.max_images = FACEBOOK_MAX_IMAGES
        self.max_video_size = FACEBOOK_MAX_VIDEO_SIZE
        self.supported_image_formats = FACEBOOK_SUPPORTED_IMAGE_FORMATS
        self.supported_video_formats = FACEBOOK_SUPPORTED_VIDEO_FORMATS
        self.media_button_xpath = "//div[@aria-label='Photo/Video']"
        self.file_input_xpath = "//input[@type='file']"
        
    def is_logged_in(self) -> bool:
        """Check if currently logged into Facebook.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Look for login button - if found, not logged in
            return not self.utils.check_login_status(self.LOGIN_BUTTON)
        except WebDriverException as e:
            self._log_error_with_trace("check_login", e, {})
            return False
            
    def login(self) -> bool:
        """Attempt to log in to Facebook.
        
        Returns:
            True if login successful, False otherwise
        """
        try:
            # Get credentials from config
            username = self.config.get("facebook", {}).get("username")
            password = self.config.get("facebook", {}).get("password")
            
            if not username or not password:
                self._log_error_with_trace(
                    "login",
                    ValueError("Missing Facebook credentials"),
                    {"username_provided": bool(username)}
                )
                return False
                
            # Navigate to Facebook
            self.driver.get(self.base_url)
            
            # Handle login
            success = self.utils.handle_login(
                username=username,
                password=password,
                username_field=self.USERNAME_FIELD,
                password_field=self.PASSWORD_FIELD,
                submit_button=self.LOGIN_BUTTON
            )
            
            if success:
                self.memory_updates["login_attempts"] += 1
                self._update_memory("login", True)
                return True
            else:
                self._update_memory("login", False)
                return False
                
        except WebDriverException as e:
            self._log_error_with_trace("login", e, {})
            self._update_memory("login", False, e)
            return False
            
    def post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Post content to Facebook.
        
        Args:
            content: Content to post
            media_paths: Optional list of media file paths
            is_video: Whether the media is video
            
        Returns:
            True if post successful, False otherwise
        """
        try:
            # Validate media if provided
            if media_paths:
                if not self._validate_media(media_paths, is_video):
                    self._log_error_with_trace(
                        "post",
                        ValueError("Invalid media files"),
                        {"media_paths": media_paths, "is_video": is_video}
                    )
                    return False
                    
            # Find post textarea
            textarea = self.utils.wait_for_element(
                By.CSS_SELECTOR,
                self.POST_TEXTAREA
            )
            if not textarea:
                self._log_error_with_trace(
                    "post",
                    ValueError("Could not find post textarea"),
                    {}
                )
                return False
                
            # Enter content
            textarea.send_keys(content)
            
            # Upload media if provided
            if media_paths:
                if not self._handle_media_upload(media_paths, is_video):
                    self._log_error_with_trace(
                        "post",
                        ValueError("Failed to upload media"),
                        {"media_paths": media_paths, "is_video": is_video}
                    )
                    return False
                    
            # Click post button
            success = self.utils.post_content(self.POST_BUTTON)
            
            if success:
                self.memory_updates["post_attempts"] += 1
                self._update_memory("post", True)
                return True
            else:
                self._update_memory("post", False)
                return False
                
        except WebDriverException as e:
            self._log_error_with_trace("post", e, {
                "content_length": len(content),
                "has_media": bool(media_paths),
                "is_video": is_video
            })
            self._update_memory("post", False, e)
            return False 