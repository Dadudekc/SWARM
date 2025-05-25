import time
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

from .platform_strategy_base import PlatformStrategy
from social.utils.social_common import SocialMediaUtils
from social.constants.platform_constants import (
    MAX_RETRIES,
    RETRY_DELAY,
    REDDIT_MAX_IMAGES,
    REDDIT_MAX_VIDEO_SIZE,
    REDDIT_SUPPORTED_IMAGE_FORMATS,
    REDDIT_SUPPORTED_VIDEO_FORMATS,
    DEFAULT_TIMEOUT
)
from dreamos.social.log_writer import logger

class RedditStrategy(PlatformStrategy):
    """Reddit platform strategy implementation."""
    
    LOGIN_URL = "https://www.reddit.com/login"
    HOME_URL = "https://www.reddit.com"
    
    def __init__(self, driver, config: dict, memory_update: dict):
        super().__init__(driver, config, memory_update)
        self.subreddit = config.get("reddit_subreddit", "DreamOS")
        self.utils = SocialMediaUtils(driver, config, "reddit")
    
    def _take_screenshot(self, context: str) -> str:
        """Take a screenshot for debugging purposes."""
        return self.utils.take_screenshot(context)
    
    def _create_media_dir(self) -> None:
        """Create media directory if it doesn't exist."""
        os.makedirs(self.utils.media_dir, exist_ok=True)
    
    def _validate_media_file(self, filepath: str) -> bool:
        """Validate media file for upload."""
        return self.utils.validate_media_file(filepath)
    
    def _wait_for_element(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """Wait for an element to be present and return it."""
        return self.utils.wait_for_element(by, value, timeout)
    
    def _wait_for_clickable(self, by: By, value: str, timeout: int = 10) -> Optional[Any]:
        """Wait for an element to be clickable and return it."""
        return self.utils.wait_for_clickable(by, value, timeout)
    
    def _retry_click(self, element, max_attempts: int = 3, delay: int = 2) -> bool:
        """Attempt to click an element with retries."""
        return self.utils.retry_click(element, max_attempts, delay)
    
    def _format_post_content(self, content: str, max_length: Optional[int] = None) -> str:
        """Format post content with optional length limit."""
        return self.utils.format_post_content(content, max_length)
    
    def _create_media_post_content(self, text: str, media_files: List[str]) -> Dict[str, Any]:
        """Create structured content for media posts."""
        return self.utils.create_media_post_content(text, media_files)
    
    def _handle_upload_error(self, error: Exception, context: str) -> bool:
        """Handle media upload errors with consistent logging and screenshots."""
        return self.utils.handle_upload_error(error, context)
    
    def _verify_post_success(self, expected_url_pattern: str, timeout: int = 10) -> bool:
        """Verify post success by checking URL pattern."""
        return self.utils.verify_post_success(expected_url_pattern, timeout)
    
    def _extract_comment_data(self, element: Any) -> Optional[Dict[str, Any]]:
        """Extract structured data from a comment element."""
        return self.utils.extract_comment_data(element)
    
    def _validate_twitter_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Validate media files for Twitter upload."""
        return self.utils.validate_twitter_media(media_paths, is_video)
    
    def _upload_twitter_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Upload media files to Twitter post."""
        return self.utils.upload_twitter_media(media_paths, is_video)
    
    def _validate_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Validate media files for Reddit upload."""
        if not media_paths:
            return True
            
        if is_video:
            if len(media_paths) > 1:
                logger.error(f"[{self.platform}] Cannot upload multiple videos in one post")
                return False
            filepath = media_paths[0]
            if not os.path.splitext(filepath)[1].lower() in REDDIT_SUPPORTED_VIDEO_FORMATS:
                logger.error(f"[{self.platform}] Unsupported video format: {filepath}")
                return False
            if not self.utils.validate_media_file(filepath, max_size_mb=100):
                return False
        else:
            if len(media_paths) > REDDIT_MAX_IMAGES:
                logger.error(f"[{self.platform}] Cannot upload more than {REDDIT_MAX_IMAGES} images")
                return False
            for filepath in media_paths:
                if not os.path.splitext(filepath)[1].lower() in REDDIT_SUPPORTED_IMAGE_FORMATS:
                    logger.error(f"[{self.platform}] Unsupported image format: {filepath}")
                    return False
                if not self.utils.validate_media_file(filepath):
                    return False
                    
        return True
    
    def _upload_media(self, media_paths: List[str], is_video: bool = False) -> bool:
        """Upload media files to Reddit post."""
        try:
            # Find and click media upload button
            media_button = self.utils.wait_for_clickable(
                By.XPATH, "//div[@data-testid='fileInput']"
            )
            if not media_button or not self.utils.retry_click(media_button):
                raise ElementClickInterceptedException("Failed to click media upload button")
            
            # Upload each file
            for filepath in media_paths:
                file_input = self.utils.wait_for_element(By.XPATH, "//input[@type='file']")
                if not file_input:
                    raise TimeoutException("File input not found")
                file_input.send_keys(os.path.abspath(filepath))
                time.sleep(2)  # Wait for upload
                
            return True
            
        except Exception as e:
            logger.error(f"[{self.platform}] Media upload error: {str(e)}")
            self.utils.take_screenshot("media_upload_error")
            return False
    
    def is_logged_in(self) -> bool:
        """Check if user is logged into Reddit."""
        try:
            # Check for login form
            login_form = self.utils.wait_for_element(
                By.XPATH,
                "//form[@action='/login']",
                timeout=5
            )
            if login_form:
                self._log_action("login_check", "not_logged_in", ["login_check"])
                return False
            
            # Check for user menu
            user_menu = self.utils.wait_for_element(
                By.XPATH,
                "//button[@data-testid='user-menu-button']",
                timeout=5
            )
            if user_menu:
                self._log_action("login_check", "logged_in", ["login_check"])
                return True
            
            return False
            
        except Exception as e:
            self._log_action("login_check", "error", ["login_check"], str(e))
            self._update_memory("check_login", False, e)
            return False
    
    def login(self) -> bool:
        """Attempt to log in to Reddit."""
        for attempt in range(MAX_RETRIES):
            try:
                self.driver.get(self.LOGIN_URL)
                time.sleep(2)
                
                # Get credentials from config
                username = self.config.get("reddit_username")
                password = self.config.get("reddit_password")
                
                if not username or not password:
                    self._log_action("login", "error", ["login"], "Missing credentials")
                    self._update_memory("login", False, ValueError("Missing credentials"))
                    return False
                
                # Find and fill username
                username_input = self.utils.wait_for_element(By.ID, "loginUsername")
                if not username_input:
                    raise TimeoutException("Username input not found")
                username_input.send_keys(username)
                
                # Find and fill password
                password_input = self.utils.wait_for_element(By.ID, "loginPassword")
                if not password_input:
                    raise TimeoutException("Password input not found")
                password_input.send_keys(password)
                
                # Click Login button
                login_button = self.utils.wait_for_clickable(By.XPATH, "//button[@type='submit']")
                if not login_button or not self.utils.retry_click(login_button):
                    raise ElementClickInterceptedException("Failed to click Login button")
                
                # Wait for login to complete
                time.sleep(5)
                
                # Verify login success
                if self.is_logged_in():
                    self._log_action("login", "success", ["login"])
                    self._update_memory("login", True)
                    return True
                else:
                    self._log_action("login", "error", ["login"], "Login verification failed")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY)
                        continue
                    return False
                    
            except Exception as e:
                self._log_action("login", "error", ["login"], str(e))
                self._update_memory("login", False, e)
                self.utils.take_screenshot(f"login_error_attempt_{attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                return False
        
        return False
    
    def post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Post content to Reddit with optional media."""
        try:
            # Navigate to subreddit
            self.driver.get(f"{self.HOME_URL}/r/{self.subreddit}/submit")
            time.sleep(2)
            
            # Select post type
            post_type = "image" if media_paths and not is_video else "video" if media_paths and is_video else "text"
            post_type_button = self.utils.wait_for_clickable(
                By.XPATH, f"//button[@data-testid='post-type-{post_type}']"
            )
            if not post_type_button or not self.utils.retry_click(post_type_button):
                raise ElementClickInterceptedException(f"Failed to select {post_type} post type")
            
            # Enter title
            title_input = self.utils.wait_for_element(By.XPATH, "//textarea[@data-testid='post-title']")
            if not title_input:
                raise TimeoutException("Title input not found")
            title_input.send_keys(content[:300])  # Reddit title limit
            
            # Handle media if provided
            if media_paths:
                if not self._validate_media(media_paths, is_video):
                    return False
                if not self._handle_media_upload(media_paths, is_video):
                    return False
            
            # Click post button
            post_button = self.utils.wait_for_clickable(By.XPATH, "//button[@data-testid='post-button']")
            if not post_button or not self.utils.retry_click(post_button):
                raise ElementClickInterceptedException("Failed to click post button")
            
            # Wait for post to complete
            time.sleep(5)
            
            # Verify post success
            if self.utils.verify_post_success(f"/r/{self.subreddit}/comments/"):
                self._log_action("post", "success", ["post"])
                self._update_memory("post", True)
                return True
            else:
                self._log_action("post", "error", ["post"], "Post verification failed")
                self._update_memory("post", False)
                return False
                
        except Exception as e:
            self._log_action("post", "error", ["post"], str(e))
            self._update_memory("post", False, e)
            self.utils.take_screenshot("post_error")
            return False
    
    def comment(self, post_url: str, content: str) -> bool:
        """Add a comment to a Reddit post."""
        try:
            self.driver.get(post_url)
            time.sleep(2)
            
            # Find comment box
            comment_box = self.utils.wait_for_element(By.XPATH, "//div[@data-testid='comment-box']")
            if not comment_box:
                raise TimeoutException("Comment box not found")
            
            # Enter comment
            comment_box.send_keys(content)
            
            # Click comment button
            comment_button = self.utils.wait_for_clickable(By.XPATH, "//button[@data-testid='comment-submit']")
            if not comment_button or not self.utils.retry_click(comment_button):
                raise ElementClickInterceptedException("Failed to click comment button")
            
            # Wait for comment to post
            time.sleep(3)
            
            # Verify comment success
            if self.utils.verify_post_success(post_url):
                self._log_action("comment", "success", ["comment"])
                self._update_memory("comment", True)
                return True
            else:
                self._log_action("comment", "error", ["comment"], "Comment verification failed")
                self._update_memory("comment", False)
                return False
                
        except Exception as e:
            self._log_action("comment", "error", ["comment"], str(e))
            self._update_memory("comment", False, e)
            self.utils.take_screenshot("comment_error")
            return False
    
    def get_post_comments(self, post_url: str) -> List[Dict[str, Any]]:
        """Get comments from a Reddit post."""
        try:
            self.driver.get(post_url)
            time.sleep(2)
            
            comments = []
            comment_elements = self.driver.find_elements(By.XPATH, "//div[@data-testid='comment']")
            
            for element in comment_elements:
                comment_data = self.utils.extract_comment_data(element)
                if comment_data:
                    comments.append(comment_data)
            
            self._log_action("get_comments", "success", ["comments"])
            self._update_memory("get_comments", True)
            return comments
            
        except Exception as e:
            self._log_action("get_comments", "error", ["comments"], str(e))
            self._update_memory("get_comments", False, e)
            self.utils.take_screenshot("get_comments_error")
            return [] 