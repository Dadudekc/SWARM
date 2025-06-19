"""
Browser Control Module
---------------------
Provides browser automation capabilities for Dream.OS.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, StaleElementReferenceException

logger = logging.getLogger("browser_control")

class BrowserControl:
    """Controls browser automation for Dream.OS."""
    
    def __init__(
        self,
        user_data_dir: str,
        window_title: str,
        page_load_wait: int = 10,
        response_wait: int = 5,
        paste_delay: float = 0.5
    ):
        """Initialize browser control.
        
        Args:
            user_data_dir: Chrome user data directory
            window_title: Window title to focus
            page_load_wait: Page load timeout in seconds
            response_wait: Response wait time in seconds
            paste_delay: Delay between paste operations
        """
        self.user_data_dir = user_data_dir
        self.window_title = window_title
        self.page_load_wait = page_load_wait
        self.response_wait = response_wait
        self.paste_delay = paste_delay
        
        self.driver = None
        self.logger = logger
    
    def start(self):
        """Start browser session."""
        try:
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = uc.Chrome(options=options)
            self.driver.set_page_load_timeout(self.page_load_wait)
            
            self.logger.info("Browser session started")
        except Exception as e:
            self.logger.error(f"Failed to start browser session: {e}")
            raise
    
    def stop(self):
        """Stop browser session."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Browser session stopped")
            except Exception as e:
                self.logger.error(f"Error stopping browser session: {e}")
                raise
    
    def navigate_to(self, url: str):
        """Navigate to URL.
        
        Args:
            url: Target URL
        """
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, self.page_load_wait).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            self.logger.info(f"Navigated to {url}")
        except TimeoutException:
            self.logger.error(f"Timeout while loading {url}")
            raise
        except WebDriverException as e:
            self.logger.error(f"Browser error while navigating to {url}: {e}")
            raise
    
    def wait_for_stable_element(
        self,
        selector: str,
        by: str = By.CSS_SELECTOR,
        stability_time: float = 2.0,
        timeout: int = 10,
        check_interval: float = 0.5
    ):
        """Wait for element to be stable (not changing).
        
        Args:
            selector: Element selector
            by: Selector type
            stability_time: Time element must be stable for
            timeout: Maximum wait time
            check_interval: Time between checks
            
        Returns:
            WebElement when stable
            
        Raises:
            TimeoutException: If element doesn't stabilize
        """
        start_time = time.time()
        last_text = None
        stable_start = None
        
        while time.time() - start_time < timeout:
            try:
                element = self.wait_for_element(selector, by, timeout=1)
                current_text = element.text
                
                if current_text == last_text:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= stability_time:
                        return element
                else:
                    stable_start = None
                    
                last_text = current_text
                time.sleep(check_interval)
            except (TimeoutException, StaleElementReferenceException):
                continue
                
        raise TimeoutException(f"Element {selector} did not stabilize within {timeout}s")
    
    def wait_for_element(self, selector: str, by: str = By.CSS_SELECTOR, timeout: Optional[int] = None):
        """Wait for element to be present.
        
        Args:
            selector: Element selector
            by: Selector type
            timeout: Wait timeout in seconds
            
        Returns:
            WebElement when found
            
        Raises:
            TimeoutException: If element not found
        """
        timeout = timeout or self.page_load_wait
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
        except TimeoutException:
            self.logger.error(f"Timeout waiting for element: {selector}")
            raise
        except WebDriverException as e:
            self.logger.error(f"Browser error while waiting for element {selector}: {e}")
            raise
    
    def send_keys(self, selector: str, text: str, by: str = By.CSS_SELECTOR):
        """Send keys to element.
        
        Args:
            selector: Element selector
            text: Text to send
            by: Selector type
            
        Raises:
            WebDriverException: If element interaction fails
        """
        try:
            element = self.wait_for_element(selector, by)
            element.clear()
            element.send_keys(text)
            time.sleep(self.paste_delay)
        except WebDriverException as e:
            self.logger.error(f"Failed to send keys to {selector}: {e}")
            raise
    
    def click(self, selector: str, by: str = By.CSS_SELECTOR):
        """Click element.
        
        Args:
            selector: Element selector
            by: Selector type
            
        Raises:
            WebDriverException: If click fails
        """
        try:
            element = self.wait_for_element(selector, by)
            element.click()
            time.sleep(self.paste_delay)
        except WebDriverException as e:
            self.logger.error(f"Failed to click {selector}: {e}")
            raise
    
    def get_text(self, selector: str, by: str = By.CSS_SELECTOR) -> str:
        """Get element text.
        
        Args:
            selector: Element selector
            by: Selector type
            
        Returns:
            Element text
            
        Raises:
            WebDriverException: If text extraction fails
        """
        try:
            element = self.wait_for_element(selector, by)
            return element.text.strip()
        except WebDriverException as e:
            self.logger.error(f"Failed to get text from {selector}: {e}")
            raise 
