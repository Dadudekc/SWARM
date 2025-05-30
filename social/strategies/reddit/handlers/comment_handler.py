from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

class CommentHandler:
    """Handles all comment-related operations for Reddit."""
    
    def __init__(self, driver, config: dict, memory_update: Optional[Dict[str, Any]] = None):
        self.driver = driver
        self.config = config
        self.memory_update = memory_update or {}
        
        # Reddit-specific selectors
        self.selectors = {
            "comment_box": "//div[@role='textbox']",
            "submit_button": "//button[@type='submit']",
            "comment_verification": "//div[contains(@class, 'Comment')]"
        }
        
    def add_comment(self, content: str) -> bool:
        """Add a comment to a Reddit post.
        
        Args:
            content: The comment content
            
        Returns:
            bool: True if comment was successful, False otherwise
        """
        try:
            # Enter comment
            comment_box = self.driver.find_element(By.XPATH, self.selectors["comment_box"])
            comment_box.send_keys(content)
            
            # Submit comment
            submit_button = self.driver.find_element(By.XPATH, self.selectors["submit_button"])
            submit_button.click()
            
            # Verify comment was posted
            return self._verify_comment_success()
            
        except (TimeoutException, ElementClickInterceptedException) as e:
            self.memory_update["last_error"] = str(e)
            return False
            
    def _verify_comment_success(self) -> bool:
        """Verify that the comment was posted successfully."""
        try:
            self.driver.find_element(By.XPATH, self.selectors["comment_verification"])
            return True
        except TimeoutException:
            return False 