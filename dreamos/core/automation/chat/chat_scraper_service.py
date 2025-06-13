"""
ChatGPT Scraper Service

Core service for scraping ChatGPT conversations and managing chat interactions.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)

from .browser_control import BrowserControl
from ..config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class ChatScraperService:
    """Core service for scraping ChatGPT conversations."""
    
    def __init__(self, config_path: str):
        """Initialize the scraper service.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_bridge_config()
        
        self.browser = BrowserControl(
            user_data_dir=self.config.get('user_data_dir'),
            window_title=self.config.get('cursor_window_title'),
            page_load_wait=self.config.get('page_load_wait', 30),
            response_wait=self.config.get('response_wait', 15),
            paste_delay=self.config.get('paste_delay', 0.5)
        )
        
        self.excluded_chats: Set[str] = set()
        self._load_exclusions()
        
    def _load_exclusions(self):
        """Load excluded chat titles."""
        exclusions_file = Path("config/excluded_chats.txt")
        if exclusions_file.exists():
            self.excluded_chats = set(exclusions_file.read_text().splitlines())
            
    def start(self):
        """Start the scraper service."""
        self.browser.start()
        logger.info("Chat scraper service started")
        
    def stop(self):
        """Stop the scraper service."""
        self.browser.stop()
        logger.info("Chat scraper service stopped")
        
    def validate_login(self) -> bool:
        """Validate ChatGPT login status.
        
        Returns:
            Whether user is logged in
        """
        try:
            self.browser.navigate_to(self.config["chatgpt_url"])
            
            # Check for login button
            try:
                login_button = self.browser.wait_for_element(
                    "button[data-testid='login-button']",
                    timeout=5
                )
                logger.warning("User not logged in")
                return False
            except TimeoutException:
                # No login button found, likely logged in
                return True
                
        except Exception as e:
            logger.error(f"Error validating login: {e}")
            return False
            
    def get_all_chats(self) -> List[Dict[str, str]]:
        """Get all chat titles and links from sidebar.
        
        Returns:
            List of dicts with chat info
        """
        logger.info("🔎 Scraping all chats from sidebar...")
        
        retry_count = 0
        max_retries = self.config.get('max_retries', 3)
        
        while retry_count < max_retries:
            try:
                # Wait for sidebar to load
                self.browser.wait_for_element(
                    "nav[data-testid='chat-list']",
                    timeout=10
                )
                
                # Get chat elements
                chat_elements = self.browser.driver.find_elements(
                    By.XPATH,
                    "//a[contains(@class, 'group') and contains(@href, '/c/')]"
                )
                
                chats = []
                for element in chat_elements:
                    try:
                        title = element.text.strip()
                        if title and title not in self.excluded_chats:
                            chats.append({
                                'title': title,
                                'link': element.get_attribute('href')
                            })
                    except StaleElementReferenceException:
                        continue
                        
                return chats
                
            except WebDriverException as e:
                logger.error(f"Browser error while scraping chats: {e}")
                retry_count += 1
                time.sleep(2 ** retry_count)  # Exponential backoff
                
            except TimeoutException as e:
                logger.error(f"Timeout while waiting for chat elements: {e}")
                retry_count += 1
                time.sleep(2 ** retry_count)
                
        return []
        
    def wait_for_stable_response(
        self,
        timeout: int = 60,
        stability_period: int = 5,
        check_interval: float = 1.0
    ) -> Optional[str]:
        """Wait for response to stabilize.
        
        Args:
            timeout: Maximum wait time
            stability_period: Time response must be stable
            check_interval: Time between checks
            
        Returns:
            Stable response text or None
        """
        start_time = time.time()
        last_response = None
        stable_start = None
        
        while time.time() - start_time < timeout:
            try:
                # Get latest response
                response_element = self.browser.wait_for_element(
                    "div[data-message-author-role='assistant']:last-child",
                    timeout=1
                )
                current_response = response_element.text.strip()
                
                if current_response == last_response:
                    if stable_start is None:
                        stable_start = time.time()
                    elif time.time() - stable_start >= stability_period:
                        return current_response
                else:
                    stable_start = None
                    
                last_response = current_response
                time.sleep(check_interval)
                
            except (TimeoutException, StaleElementReferenceException):
                continue
                
        return last_response
        
    def send_prompt(self, prompt: str) -> Optional[str]:
        """Send prompt and wait for response.
        
        Args:
            prompt: Prompt to send
            
        Returns:
            Response text or None
        """
        try:
            # Wait for input
            self.browser.wait_for_stable_element(
                "textarea",
                by=By.TAG_NAME,
                stability_time=2.0
            )
            
            # Send prompt
            self.browser.send_keys("textarea", prompt)
            self.browser.click("button[type='submit']")
            
            # Wait for response
            return self.wait_for_stable_response()
            
        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            return None
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.browser.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 