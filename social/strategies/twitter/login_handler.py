"""
Twitter Login Handler
-------------------
Handles Twitter authentication and session management.
"""

from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

class LoginHandler:
    """Handles Twitter login operations."""
    
    SESSION_TIMEOUT = timedelta(hours=24)  # Session timeout period
    
    def __init__(self, driver, config: Dict[str, Any], memory_update: Optional[Dict[str, Any]] = None):
        """Initialize the login handler.
        
        Args:
            driver: Selenium WebDriver instance
            config: Configuration dictionary
            memory_update: Optional memory update dictionary
        """
        self.driver = driver
        self.config = config
        self.memory_update = memory_update or {}
        self.credentials = config.get('twitter', {}).get('credentials', {})
        self._session_file = Path(config.get('twitter', {}).get('session_path', 'runtime/sessions/twitter_session.json'))
        self._session = None
        self._last_error = None
        self._last_action = None
        
    def login(self) -> bool:
        """Login to Twitter.
        
        Returns:
            True if login was successful, False otherwise
        """
        try:
            # Try to load existing session first
            if self._load_session():
                return True
                
            # Enter username
            username_input = self.driver.find_element(By.NAME, "text")
            username_input.send_keys(self.credentials.get('username', ''))
            
            # Click next
            next_button = self.driver.find_element(By.XPATH, "//span[text()='Next']")
            next_button.click()
            
            # Enter password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(self.credentials.get('password', ''))
            
            # Click login
            login_button = self.driver.find_element(By.XPATH, "//span[text()='Log in']")
            login_button.click()
            
            # Verify login success
            if self._verify_login():
                self._save_session()
                return True
                
            return False
            
        except (TimeoutException, NoSuchElementException) as e:
            self._last_error = {
                "error": str(e),
                "context": "login",
                "timestamp": datetime.now().isoformat()
            }
            return False
            
    def _verify_login(self) -> bool:
        """Verify that login was successful.
        
        Returns:
            True if login was verified, False otherwise
        """
        try:
            # Check for user menu
            user_menu = self.driver.find_element(
                By.XPATH,
                "//button[contains(@class, 'user-menu')] | //a[contains(@href, '/logout')]"
            )
            return user_menu is not None
        except (TimeoutException, NoSuchElementException):
            return False
            
    def _save_session(self) -> None:
        """Save current session state."""
        try:
            session_data = {
                'cookies': self.driver.get_cookies(),
                'timestamp': datetime.now().isoformat()
            }
            
            # Ensure directory exists
            self._session_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._session_file, 'w') as f:
                json.dump(session_data, f)
                
        except Exception as e:
            self._last_error = {
                "error": str(e),
                "context": "save_session",
                "timestamp": datetime.now().isoformat()
            }
    
    def _load_session(self) -> bool:
        """Load existing session if available.
        
        Returns:
            True if session loaded successfully, False otherwise
        """
        try:
            if not self._session_file.exists():
                return False
                
            with open(self._session_file, 'r') as f:
                session_data = json.load(f)
                
            # Check if session is still valid
            timestamp = datetime.fromisoformat(session_data['timestamp'])
            if datetime.now() - timestamp > self.SESSION_TIMEOUT:
                return False
                
            # Restore cookies
            for cookie in session_data['cookies']:
                self.driver.add_cookie(cookie)
                
            # Verify session
            return self._verify_login()
                
        except Exception as e:
            self._last_error = {
                "error": str(e),
                "context": "load_session",
                "timestamp": datetime.now().isoformat()
            }
            return False
            
    def refresh_session(self) -> bool:
        """Refresh login session.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clear existing session
            if self._session_file.exists():
                os.remove(self._session_file)
                
            # Perform new login
            return self.login()
            
        except Exception as e:
            self._last_error = {
                "error": str(e),
                "context": "refresh_session",
                "timestamp": datetime.now().isoformat()
            }
            return False 
