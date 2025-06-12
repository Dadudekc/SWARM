"""
Handles posting to social media platforms using browser automation.
Uses undetected-chromedriver for stealth and session persistence.
"""

import os
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.file_ops import ensure_dir
from dreamos.social.utils.social_common import SocialConfig
from dreamos.core.security.session_manager import SessionManager
from dreamos.social.platform_login import PlatformLoginManager

logger = get_logger(__name__)

class SelectorError(Exception):
    """Raised when a selector fails to find an element."""
    pass

class PlatformPoster:
    """Handles posting to social media platforms using browser automation."""
    
    def __init__(self, config: Optional[SocialConfig] = None):
        self.config = config or SocialConfig()
        self.session_manager = SessionManager()
        self.login_manager = PlatformLoginManager(config)
        self.driver = None
        self.selector_file = Path("dreamos/social/selectors/selector_diagnostic.md")
        self.request_file = Path("dreamos/social/selectors/collector_request.json")
        self._load_selectors()
        
    def _load_selectors(self):
        """Load platform-specific selectors from diagnostic file."""
        if not self.selector_file.exists():
            logger.warning("Selector diagnostic file not found: %s", self.selector_file)
            self.selectors = {}
            return
            
        try:
            with open(self.selector_file, 'r') as f:
                content = f.read()
                # Parse markdown sections into selector dict
                self.selectors = self._parse_selector_markdown(content)
        except Exception as e:
            logger.error("Failed to load selectors: %s", e)
            self.selectors = {}
            
    def _parse_selector_markdown(self, content: str) -> Dict[str, Dict[str, str]]:
        """Parse markdown selector documentation into structured data."""
        selectors = {}
        current_platform = None
        
        for line in content.split('\n'):
            if line.startswith('## '):
                current_platform = line[3:].strip().lower()
                selectors[current_platform] = {}
            elif line.startswith('* ') and current_platform:
                # Parse selector line: * element_name: selector_value
                try:
                    name, selector = line[2:].split(':', 1)
                    selectors[current_platform][name.strip()] = selector.strip()
                except ValueError:
                    continue
                    
        return selectors
        
    def _request_selector(self, platform: str, element: str):
        """Request a new selector from Victor."""
        request = {
            "platform": platform,
            "element": element,
            "timestamp": time.time(),
            "status": "pending"
        }
        
        ensure_dir(self.request_file.parent)
        with open(self.request_file, 'w') as f:
            json.dump(request, f, indent=2)
            
        logger.info("Selector request logged for Victor: %s/%s", platform, element)
        raise SelectorError(f"Missing selector for {platform}/{element}. Request logged for Victor.")
        
    def _get_selector(self, platform: str, element: str) -> str:
        """Get selector for platform element, request if missing."""
        platform = platform.lower()
        if platform not in self.selectors:
            self._request_selector(platform, element)
            
        selector = self.selectors[platform].get(element)
        if not selector:
            self._request_selector(platform, element)
            
        return selector
        
    def _wait_for_element(self, selector: str, timeout: int = 10):
        """Wait for element to be present and visible."""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            return element
        except TimeoutException:
            raise SelectorError(f"Timeout waiting for element: {selector}")
            
    def _ensure_logged_in(self, platform: str):
        """Ensure we're logged into the platform."""
        if not self.driver:
            self.driver = self.login_manager.get_driver()
            
        # Check login status
        try:
            if platform == "twitter":
                self.driver.get("https://twitter.com/home")
                if "login" in self.driver.current_url:
                    self.login_manager.login_twitter()
            elif platform == "reddit":
                self.driver.get("https://www.reddit.com/submit")
                if "login" in self.driver.current_url:
                    self.login_manager.login_reddit()
            # Add other platforms...
        except Exception as e:
            logger.error("Login check failed for %s: %s", platform, e)
            raise
            
    def post(self, platform: str, content: str, **kwargs) -> bool:
        """Post content to specified platform."""
        try:
            self._ensure_logged_in(platform)
            
            if platform == "twitter":
                return self._post_to_twitter(content)
            elif platform == "reddit":
                return self._post_to_reddit(content, **kwargs)
            # Add other platforms...
            else:
                logger.error("Unsupported platform: %s", platform)
                return False
                
        except SelectorError as e:
            logger.error("Selector error: %s", e)
            return False
        except Exception as e:
            logger.exception("Posting failed: %s", e)
            return False
            
    def _post_to_twitter(self, content: str) -> bool:
        """Post to Twitter using browser automation."""
        try:
            # Navigate to compose tweet
            self.driver.get("https://twitter.com/compose/tweet")
            time.sleep(3)
            
            # Find tweet input
            tweet_input = self._wait_for_element(
                self._get_selector("twitter", "tweet_input")
            )
            tweet_input.send_keys(content)
            
            # Click tweet button
            tweet_button = self._wait_for_element(
                self._get_selector("twitter", "tweet_button")
            )
            tweet_button.click()
            
            # Wait for success
            time.sleep(3)
            return True
            
        except Exception as e:
            logger.error("Twitter post failed: %s", e)
            return False
            
    def _post_to_reddit(self, content: str, subreddit: str = None) -> bool:
        """Post to Reddit using browser automation."""
        try:
            # Navigate to submit page
            if subreddit:
                self.driver.get(f"https://www.reddit.com/r/{subreddit}/submit")
            else:
                self.driver.get("https://www.reddit.com/submit")
            time.sleep(3)
            
            # Select text post
            text_post = self._wait_for_element(
                self._get_selector("reddit", "text_post_button")
            )
            text_post.click()
            
            # Fill title and content
            title_input = self._wait_for_element(
                self._get_selector("reddit", "title_input")
            )
            title_input.send_keys(content[:300])  # Reddit title limit
            
            content_input = self._wait_for_element(
                self._get_selector("reddit", "content_input")
            )
            content_input.send_keys(content)
            
            # Click submit
            submit_button = self._wait_for_element(
                self._get_selector("reddit", "submit_button")
            )
            submit_button.click()
            
            # Wait for success
            time.sleep(5)
            return True
            
        except Exception as e:
            logger.error("Reddit post failed: %s", e)
            return False
            
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None 