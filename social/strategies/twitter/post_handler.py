"""
Twitter Post Handler
------------------
Handles post creation and verification for Twitter.
"""

from typing import Optional, List
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class PostHandler:
    """Handles Twitter post operations."""
    
    def __init__(self, driver, config):
        """Initialize the post handler.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
        """
        self.driver = driver
        self.config = config
        
    def create_post(self, title: str, content: str, media_files: Optional[List[str]] = None) -> bool:
        """Create a post on Twitter.
        
        Args:
            title: Post title (unused for Twitter)
            content: Post content
            media_files: Optional list of media files to attach
            
        Returns:
            True if post was successful, False otherwise
        """
        try:
            # Click compose button
            compose_button = self.driver.find_element(By.XPATH, "//a[@href='/compose/tweet']")
            compose_button.click()
            
            # Enter post content
            post_input = self.driver.find_element(By.XPATH, "//div[@role='textbox']")
            post_input.send_keys(content)
            
            # Handle media if provided
            if media_files:
                self._attach_media(media_files)
            
            # Click post button
            post_button = self.driver.find_element(By.XPATH, "//div[@data-testid='tweetButton']")
            post_button.click()
            
            # Verify post was created
            return self._verify_post(content)
            
        except (TimeoutException, NoSuchElementException) as e:
            return False
            
    def _attach_media(self, media_files: List[str]) -> None:
        """Attach media files to the post.
        
        Args:
            media_files: List of media file paths
        """
        # Click media button
        media_button = self.driver.find_element(By.XPATH, "//input[@data-testid='fileInput']")
        
        # Upload each file
        for file_path in media_files:
            media_button.send_keys(file_path)
            
    def _verify_post(self, content: str) -> bool:
        """Verify that the post was created successfully.
        
        Args:
            content: Expected post content
            
        Returns:
            True if post was verified, False otherwise
        """
        try:
            # Wait for post to appear in timeline
            post = self.driver.find_element(
                By.XPATH,
                f"//article[contains(., '{content}')]"
            )
            return post is not None
        except (TimeoutException, NoSuchElementException):
            return False 