from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

class PostHandler:
    def __init__(self, driver: WebDriver, config: dict):
        self.driver = driver
        self.config = config
        self.utils = None  # Will be set by RedditStrategy
        
        # Selectors for Reddit post elements
        self.selectors = {
            "title_input": "//textarea[@name='title']",
            "content_input": "//div[@role='textbox']",
            "submit_button": "//button[@type='submit']",
            "media_upload": "//button[contains(@class, 'media-upload')]",
            "file_input": "//input[@type='file']",
            "upload_complete": "//div[contains(@class, 'upload-complete')]",
            "post_content": "//div[@class='post-content']"
        }

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
            subreddit = self.config.get('reddit', {}).get('subreddit', 'test')
            self.driver.get(f"https://www.reddit.com/r/{subreddit}/submit")
            
            # Find and fill content
            content_input = self.utils.wait_for_element(By.XPATH, self.selectors["content_input"])
            if not content_input:
                return False
            content_input.send_keys(content)
                
            # Handle media if provided
            if media_paths:
                # Find upload button
                upload_button = self.utils.wait_for_clickable(By.XPATH, self.selectors["media_upload"])
                if not upload_button:
                    return False
                    
                # Click upload button
                if not self.utils.retry_click(upload_button):
                    return False
                    
                # Find file input
                file_input = self.utils.wait_for_element(By.XPATH, self.selectors["file_input"])
                if not file_input:
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
                        return False
            
            # Submit post
            submit_button = self.utils.wait_for_clickable(By.XPATH, self.selectors["submit_button"])
            if not submit_button:
                return False
                
            # Click with retry
            if not self.utils.retry_click(submit_button):
                return False
                
            # Verify post success
            if not self.utils.wait_for_element(By.XPATH, self.selectors["post_content"], timeout=10):
                return False
                
            return True
            
        except Exception:
            return False 
