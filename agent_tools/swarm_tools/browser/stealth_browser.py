"""Main stealth browser implementation."""
import logging
import time
from typing import Optional, Dict, Any
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .config import DEFAULT_CONFIG
from .cookie_manager import CookieManager
from .login_handler import LoginHandler

class StealthBrowser:
    """Codex-compatible synchronous stealth browser."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger("StealthBrowser")
        self.config = {**DEFAULT_CONFIG, **(config or {})}
        self.driver = None
        self.cookie_manager = CookieManager(cookies_file=self.config['cookies_file'])
        self.login_handler = None

    def start(self):
        """Launch stealth browser session."""
        options = uc.ChromeOptions()
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size={},{}'.format(*self.config['window_size']))
        if self.config['headless']:
            options.add_argument('--headless')
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(self.config['page_load_wait'])
        
        # Initialize handlers
        self.cookie_manager.set_driver(self.driver)
        self.login_handler = LoginHandler(self.driver, self.config)

    def stop(self):
        """Stop browser session."""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def navigate_to(self, url: Optional[str] = None):
        """Navigate to a target URL."""
        target = url or self.config['target_url']
        self.logger.info(f"Navigating to {target}")
        self.driver.get(target)
        # Wait for page load and JS initialization
        WebDriverWait(self.driver, self.config['page_load_wait']).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )

    def check_login_status(self) -> bool:
        """Check if we're logged in by looking for elements that only appear when logged in."""
        try:
            # Wait a moment for the page to load
            time.sleep(2)
            
            # Check for elements that indicate we're logged in
            selectors = [
                self.config['codex_selectors']['code_input'],
                'textarea[data-testid="code-input"]',
                'div[data-testid="response-area"]'
            ]
            
            for selector in selectors:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        self.logger.info("Login status: Logged in")
                        return True
                except:
                    continue
            
            self.logger.info("Login status: Not logged in")
            return False
        except Exception as e:
            self.logger.error(f"Error checking login status: {str(e)}")
            return False

    def print_element_info(self, selector: str, by: str = By.CSS_SELECTOR):
        """Print detailed information about an element for debugging."""
        try:
            element = self.login_handler.find_element(selector, by)
            if element:
                print(f"\nElement found with selector: {selector}")
                print(f"Tag name: {element.tag_name}")
                print(f"ID: {element.get_attribute('id')}")
                print(f"Class: {element.get_attribute('class')}")
                print(f"Name: {element.get_attribute('name')}")
                print(f"Type: {element.get_attribute('type')}")
                print(f"Placeholder: {element.get_attribute('placeholder')}")
                print(f"Value: {element.get_attribute('value')}")
                return element
            else:
                print(f"\nNo element found with selector: {selector}")
                return None
        except Exception as e:
            print(f"\nError finding element: {str(e)}")
            return None 
