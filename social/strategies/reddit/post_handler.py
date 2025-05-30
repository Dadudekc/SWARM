from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

class PostHandler:
    def __init__(self, driver: WebDriver, config: dict):
        self.driver = driver
        self.config = config
        self.utils = None  # Will be set by RedditStrategy

    def create_post(self, content: str, media_paths: Optional[List[str]] = None, is_video: bool = False) -> bool:
        """Create a new post on Reddit.
        
        Args:
            content: Content of the post
            media_paths: Optional list of media file paths
            is_video: Whether the media is video
            
        Returns:
            bool: True if post was successful, False otherwise
        """
        try:
            # Navigate to submit page
            self.driver.get(f"https://www.reddit.com/r/{self.config.get('reddit', {}).get('subreddit', 'test')}/submit")
            
            # Find and fill title
            title_field = self.utils.wait_for_element(By.XPATH, "//textarea[@name='title']")
            if not title_field:
                return False
            title_field.send_keys(content[:300])  # Reddit title limit
            
            # Find and fill text if content is longer
            if len(content) > 300:
                text_field = self.utils.wait_for_element(By.XPATH, "//div[@role='textbox']")
                if not text_field:
                    return False
                text_field.send_keys(content[300:])
                
            # Upload media if provided
            if media_paths:
                # Find upload button
                upload_button = self.utils.wait_for_clickable(By.XPATH, "//button[contains(@class, 'media-upload')]")
                if not upload_button:
                    return False
                    
                # Click upload button
                if not self.utils.retry_click(upload_button):
                    return False
                    
                # Find file input
                file_input = self.utils.wait_for_element(By.XPATH, "//input[@type='file']")
                if not file_input:
                    return False
                    
                # Upload each file
                for file_path in media_paths:
                    file_input.send_keys(file_path)
                    
                    # Wait for upload to complete
                    if not self.utils.wait_for_element(
                        By.XPATH,
                        "//div[contains(@class, 'upload-complete')]",
                        timeout=30
                    ):
                        return False
                    
            # Find and click submit button
            submit_button = self.utils.wait_for_clickable(By.XPATH, "//button[@type='submit']")
            if not submit_button:
                return False
                
            # Click with retry
            if not self.utils.retry_click(submit_button):
                return False
                
            # Verify post success
            if not self.utils.wait_for_element(By.XPATH, "//div[@class='post-content']", timeout=10):
                return False
                
            return True
            
        except Exception:
            return False 