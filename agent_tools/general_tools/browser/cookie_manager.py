"""Cookie management functionality for the stealth browser."""
import json
import os
import logging
from typing import Optional, Dict, Any
from selenium.webdriver.remote.webdriver import WebDriver

class CookieManager:
    """Handles saving and loading of browser cookies."""
    
    def __init__(self, driver: Optional[WebDriver] = None, cookies_file: str = 'codex_cookies.json'):
        self.logger = logging.getLogger("CookieManager")
        self.driver = driver
        self.cookies_file = cookies_file

    def set_driver(self, driver: WebDriver):
        """Set the WebDriver instance."""
        self.driver = driver

    def save_cookies(self) -> bool:
        """Save current cookies to file."""
        try:
            if not self.driver:
                return False
            
            cookies = self.driver.get_cookies()
            with open(self.cookies_file, 'w') as f:
                json.dump(cookies, f)
            self.logger.info(f"Cookies saved to {self.cookies_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving cookies: {str(e)}")
            return False

    def load_cookies(self) -> bool:
        """Load cookies from file and add them to the current session."""
        try:
            if not os.path.exists(self.cookies_file):
                self.logger.info("No cookies file found")
                return False
            
            with open(self.cookies_file, 'r') as f:
                cookies = json.load(f)
            
            # First navigate to the domain
            self.driver.get('https://chat.openai.com')
            
            # Add each cookie
            for cookie in cookies:
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    self.logger.warning(f"Could not add cookie: {str(e)}")
            
            # Refresh page to apply cookies
            self.driver.refresh()
            
            self.logger.info("Cookies loaded successfully")
            return True
        except Exception as e:
            self.logger.error(f"Error loading cookies: {str(e)}")
            return False 