from typing import Optional, List, Dict, Any
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

class PostHandler:
    """Handles all post-related operations for Reddit."""
    
    def __init__(self, driver, config: dict, memory_update: Optional[Dict[str, Any]] = None):
        self.driver = driver
        self.config = config
        self.memory_update = memory_update or {}
        
        # Reddit-specific selectors
        self.selectors = {
            "post_button": "//button[contains(text(), 'Post')]",
            "title_input": "//textarea[@placeholder='Title']",
            "content_input": "//div[@role='textbox']",
            "submit_button": "//button[@type='submit']",
            "post_verification": "//div[contains(@class, 'Post')]"
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
            # Click post button
            post_button = self.driver.find_element(By.XPATH, self.selectors["post_button"])
            post_button.click()
            
            # Enter title and content
            title_input = self.driver.find_element(By.XPATH, self.selectors["title_input"])
            title_input.send_keys(content[:100])  # Reddit title limit
            
            content_input = self.driver.find_element(By.XPATH, self.selectors["content_input"])
            content_input.send_keys(content)
            
            # Handle media if provided
            if media_paths:
                self._handle_media_upload(media_paths, is_video)
            
            # Submit post
            submit_button = self.driver.find_element(By.XPATH, self.selectors["submit_button"])
            submit_button.click()
            
            # Verify post was created
            return self._verify_post_success()
            
        except (TimeoutException, ElementClickInterceptedException) as e:
            self.memory_update["last_error"] = str(e)
            return False
            
    def _handle_media_upload(self, media_paths: List[str], is_video: bool) -> None:
        """Handle media file upload for posts."""
        # TODO: Implement media upload logic
        pass
        
    def _verify_post_success(self) -> bool:
        """Verify that the post was created successfully."""
        try:
            self.driver.find_element(By.XPATH, self.selectors["post_verification"])
            return True
        except TimeoutException:
            return False 