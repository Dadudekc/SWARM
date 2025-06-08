from typing import Optional, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException
)

class PostHandler:
    """Handles all post-related operations for Reddit."""
    
    def __init__(self, driver, config: dict, memory_update: Optional[Dict[str, Any]] = None):
        self.driver = driver
        self.config = config
        self.memory_update = memory_update or {}
        self.utils = None  # Will be set by RedditStrategy
        
        # Reddit-specific selectors
        self.selectors = {
            "post_button": "//button[contains(text(), 'Post')]",
            "title_input": "//textarea[@name='title']",
            "content_input": "//div[@role='textbox']",
            "submit_button": "//button[@type='submit']",
            "post_verification": "//div[contains(@class, 'Post')]",
            "media_upload": "//button[contains(@class, 'media-upload')]",
            "file_input": "//input[@type='file']",
            "upload_complete": "//div[contains(@class, 'upload-complete')]"
        }
        
    def create_post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Create a new post on Reddit.
        
        Args:
            content: The post content
            media_paths: Optional list of media file paths
            is_video: Whether the media is video
            
        Returns:
            bool: True if post was successful, False otherwise
        """
        try:
            # Navigate to submit page
            subreddit = self.config.get('reddit', {}).get('subreddit', 'test')
            self.driver.get(f"https://www.reddit.com/r/{subreddit}/submit")
            
            # Find and fill title
            title_input = self.utils.wait_for_element(By.XPATH, self.selectors["title_input"])
            if not title_input:
                self.memory_update["last_error"] = {
                    "error": "Title input not found",
                    "context": "create_post"
                }
                return False
            title_input.send_keys(content[:300])  # Reddit title limit
            
            # Find and fill text if content is longer
            if len(content) > 300:
                content_input = self.utils.wait_for_element(By.XPATH, self.selectors["content_input"])
                if not content_input:
                    self.memory_update["last_error"] = {
                        "error": "Content input not found",
                        "context": "create_post"
                    }
                    return False
                content_input.send_keys(content[300:])
                
            # Handle media if provided
            if media_paths:
                if not self._handle_media_upload(media_paths, is_video):
                    return False
            
            # Submit post
            submit_button = self.utils.wait_for_clickable(By.XPATH, self.selectors["submit_button"])
            if not submit_button:
                self.memory_update["last_error"] = {
                    "error": "Post verification failed",
                    "context": "create_post"
                }
                return False
                
            # Click with retry
            if not self.utils.retry_click(submit_button):
                self.memory_update["last_error"] = {
                    "error": "Post verification failed",
                    "context": "create_post"
                }
                return False
            
            # Verify post was created
            return self._verify_post_success()
            
        except (TimeoutException, ElementClickInterceptedException, NoSuchElementException, WebDriverException) as e:
            self.memory_update["last_error"] = {
                "error": str(e),
                "context": "create_post"
            }
            return False
            
    def _handle_media_upload(self, media_paths: List[str], is_video: bool) -> bool:
        """Handle media file upload for posts."""
        try:
            # Find upload button
            upload_button = self.utils.wait_for_clickable(By.XPATH, self.selectors["media_upload"])
            if not upload_button:
                self.memory_update["last_error"] = {
                    "error": "Media upload button not found",
                    "context": "media_upload"
                }
                return False
                
            # Click upload button
            if not self.utils.retry_click(upload_button):
                self.memory_update["last_error"] = {
                    "error": "Failed to click upload button",
                    "context": "media_upload"
                }
                return False
                
            # Find file input
            file_input = self.utils.wait_for_element(By.XPATH, self.selectors["file_input"])
            if not file_input:
                self.memory_update["last_error"] = {
                    "error": "File input not found",
                    "context": "media_upload"
                }
                return False
                
            # Upload each file
            for file_path in media_paths:
                file_input.send_keys(file_path)
                
                # Wait for upload to complete
                if not self.utils.wait_for_element(
                    By.XPATH,
                    self.selectors["upload_complete"],
                    timeout=30
                ):
                    self.memory_update["last_error"] = {
                        "error": "Media upload timed out",
                        "context": "media_upload"
                    }
                    return False
                    
            return True
            
        except Exception as e:
            self.memory_update["last_error"] = {
                "error": str(e),
                "context": "media_upload"
            }
            return False
        
    def _verify_post_success(self) -> bool:
        """Verify that the post was created successfully."""
        try:
            return bool(self.utils.wait_for_element(
                By.XPATH,
                self.selectors["post_verification"],
                timeout=10
            ))
        except TimeoutException:
            self.memory_update["last_error"] = {
                "error": "Post verification timed out",
                "context": "verify_post"
            }
            return False 
