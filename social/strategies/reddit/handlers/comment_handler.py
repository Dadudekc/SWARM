from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException
)

class CommentHandler:
    """Handles all comment-related operations for Reddit."""
    
    def __init__(self, driver, config: dict, memory_update: Optional[Dict[str, Any]] = None):
        self.driver = driver
        self.config = config
        self.memory_update = memory_update or {}
        self.utils = None  # Will be set by RedditStrategy
        
        # Reddit-specific selectors
        self.selectors = {
            "comment_box": "//div[@role='textbox']",
            "submit_button": "//button[@type='submit']",
            "comment_verification": "//div[contains(@class, 'Comment')]",
            "comment_form": "//form[contains(@class, 'comment-form')]"
        }
        
    def add_comment(self, content: str) -> bool:
        """Add a comment to a Reddit post.
        
        Args:
            content: The comment content
            
        Returns:
            bool: True if comment was successful, False otherwise
        """
        try:
            # Find comment form
            comment_form = self.utils.wait_for_element(By.XPATH, self.selectors["comment_form"])
            if not comment_form:
                self.memory_update["last_error"] = {
                    "error": "Comment form not found",
                    "context": "add_comment"
                }
                return False
            
            # Find and fill comment box
            comment_box = self.utils.wait_for_element(By.XPATH, self.selectors["comment_box"])
            if not comment_box:
                self.memory_update["last_error"] = {
                    "error": "Comment box not found",
                    "context": "add_comment"
                }
                return False
            comment_box.send_keys(content)
            
            # Find and click submit button
            submit_button = self.utils.wait_for_clickable(By.XPATH, self.selectors["submit_button"])
            if not submit_button:
                self.memory_update["last_error"] = {
                    "error": "Submit button not found",
                    "context": "add_comment"
                }
                return False
            
            # Click with retry
            if not self.utils.retry_click(submit_button):
                self.memory_update["last_error"] = {
                    "error": "Failed to click submit button",
                    "context": "add_comment"
                }
                return False
            
            # Verify comment was posted
            return self._verify_comment_success()
            
        except (TimeoutException, ElementClickInterceptedException, NoSuchElementException, WebDriverException) as e:
            self.memory_update["last_error"] = {
                "error": str(e),
                "context": "add_comment"
            }
            return False
            
    def _verify_comment_success(self) -> bool:
        """Verify that the comment was posted successfully."""
        try:
            return bool(self.utils.wait_for_element(
                By.XPATH,
                self.selectors["comment_verification"],
                timeout=10
            ))
        except TimeoutException:
            self.memory_update["last_error"] = {
                "error": "Comment verification timed out",
                "context": "verify_comment"
            }
            return False 
