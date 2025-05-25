import os
from typing import Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dreamos.social.log_writer import logger

class DriverUtils:
    """Utility methods for driver operations."""
    
    def __init__(self, driver: Any, wait_timeout: int = 30):
        self.driver = driver
        self.wait_timeout = wait_timeout
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Any:
        """Wait for an element to be present and return it."""
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"[Driver] Timeout waiting for element {value}: {str(e)}")
            raise
    
    def is_element_present(self, by: By, value: str) -> bool:
        """Check if an element is present."""
        try:
            self.driver.find_element(by, value)
            return True
        except:
            return False
    
    def execute_js(self, script: str, *args) -> Any:
        """Execute JavaScript code."""
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"[Driver] Error executing JavaScript: {str(e)}")
            raise
    
    def take_screenshot(self, filename: str) -> str:
        """Take a screenshot and save it."""
        try:
            screenshot_dir = os.path.join(os.getcwd(), "social", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"[Driver] Saved screenshot to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"[Driver] Error taking screenshot: {str(e)}")
            raise 