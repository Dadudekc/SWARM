"""
Browser Control Module
---------------------
Provides browser automation capabilities for Dream.OS.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

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
        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={self.user_data_dir}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(self.page_load_wait)
        
        self.logger.info("Browser session started")
    
    def stop(self):
        """Stop browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logger.info("Browser session stopped")
    
    def navigate_to(self, url: str):
        """Navigate to URL.
        
        Args:
            url: Target URL
        """
        self.driver.get(url)
        WebDriverWait(self.driver, self.page_load_wait).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        self.logger.info(f"Navigated to {url}")
    
    def wait_for_element(self, selector: str, by: str = By.CSS_SELECTOR, timeout: Optional[int] = None):
        """Wait for element to be present.
        
        Args:
            selector: Element selector
            by: Selector type
            timeout: Wait timeout in seconds
            
        Returns:
            WebElement when found
        """
        timeout = timeout or self.page_load_wait
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    
    def send_keys(self, selector: str, text: str, by: str = By.CSS_SELECTOR):
        """Send keys to element.
        
        Args:
            selector: Element selector
            text: Text to send
            by: Selector type
        """
        element = self.wait_for_element(selector, by)
        element.clear()
        element.send_keys(text)
        time.sleep(self.paste_delay)
    
    def click(self, selector: str, by: str = By.CSS_SELECTOR):
        """Click element.
        
        Args:
            selector: Element selector
            by: Selector type
        """
        element = self.wait_for_element(selector, by)
        element.click()
        time.sleep(self.paste_delay)
    
    def get_text(self, selector: str, by: str = By.CSS_SELECTOR) -> str:
        """Get element text.
        
        Args:
            selector: Element selector
            by: Selector type
            
        Returns:
            Element text
        """
        element = self.wait_for_element(selector, by)
        return element.text.strip() 