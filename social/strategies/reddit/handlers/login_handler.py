"""
Reddit Login Handler
------------------
Handles Reddit login operations and session management.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    WebDriverException
)
from datetime import datetime, timedelta
import time
import json
import re
from dataclasses import dataclass
from pathlib import Path
from dreamos.core.log_manager import LogManager
from dreamos.social.utils.social_common import SocialMediaUtils
from dreamos.core.logging.log_config import LogLevel
from ..config import RedditConfig

logger = logging.getLogger(__name__)

@dataclass
class LoginCredentials:
    """Reddit login credentials."""
    username: str
    password: str
    client_id: str
    client_secret: str
    user_agent: str

@dataclass
class LoginSession:
    """Reddit login session."""
    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str
    token_type: str

class LoginError(Exception):
    """Login error."""
    pass

class LoginHandler:
    """Handles Reddit login operations."""
    
    LOGIN_URL = "https://www.reddit.com/login"
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    SESSION_TIMEOUT = timedelta(hours=24)
    
    def __init__(self, driver, config: RedditConfig, memory_update: Optional[Dict[str, Any]] = None, logger: Optional[LogManager] = None):
        """Initialize login handler.
        
        Args:
            driver: Selenium WebDriver instance
            config: RedditConfig instance
            memory_update: Optional dictionary to store memory updates
            logger: Optional LogManager instance
        """
        self.driver = driver
        self.config = config
        self.logger = logger or LogManager(level=LogLevel.INFO)
        self.memory_updates = memory_update or {"stats": {"is_logged_in": False}}
        self.selectors = {
            "username_input": "//input[@id='loginUsername']",
            "password_input": "//input[@id='loginPassword']",
            "submit_button": "//button[@type='submit']",
            "user_menu": "//div[@data-testid='user-menu']",
            "login_form": "//form[@id='login-form']",
            "error_message": "//div[contains(@class, 'error-message')]"
        }
        self.session_cookie_name = "session"
        self.last_login_attempt = None
        self.login_attempts = 0
        self._credentials: Optional[LoginCredentials] = None
        self._session: Optional[LoginSession] = None
        self._session_file = self.config.cookies_path / "reddit_session.json"
        self._session_file.parent.mkdir(parents=True, exist_ok=True)
        self._last_action = None
        self._last_error = None
        self.utils = SocialMediaUtils(driver, self.config.__dict__)
        
        # Load existing session if available
        self._load_session()
    
    def set_credentials(self, credentials: LoginCredentials) -> None:
        """Set login credentials.
        
        Args:
            credentials: Login credentials
        """
        self._credentials = credentials
    
    def validate_credentials(self) -> bool:
        """Validate login credentials.
        
        Returns:
            True if valid, False otherwise
        """
        if not self._credentials:
            self._last_error = {"error": "No credentials provided", "context": "missing_credentials"}
            return False
            
        # Check required fields
        required_fields = ['username', 'password', 'client_id', 'client_secret', 'user_agent']
        for field in required_fields:
            if not getattr(self._credentials, field):
                self._last_error = {"error": f"Missing required field: {field}", "context": "missing_field"}
                return False
                
        # Validate username format
        if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', self._credentials.username):
            self._last_error = {"error": "Invalid username format", "context": "invalid_username"}
            return False
            
        # Validate password length
        if len(self._credentials.password) < 8:
            self._last_error = {"error": "Password too short", "context": "invalid_password"}
            return False
            
        # Validate client ID format
        if not re.match(r'^[a-zA-Z0-9_-]{14}$', self._credentials.client_id):
            self._last_error = {"error": "Invalid client ID format", "context": "invalid_client_id"}
            return False
            
        # Validate client secret format
        if not re.match(r'^[a-zA-Z0-9_-]{27}$', self._credentials.client_secret):
            self._last_error = {"error": "Invalid client secret format", "context": "invalid_client_secret"}
            return False
            
        return True
    
    def _validate_session_cookie(self) -> bool:
        """Validate session cookie.
        
        Returns:
            True if session is valid, False otherwise
        """
        try:
            cookies = self.driver.get_cookies()
            session_cookie = next(
                (cookie for cookie in cookies if cookie['name'] == self.session_cookie_name),
                None
            )
            return session_cookie is not None
        except Exception as e:
            self.logger.error(f"Error validating session cookie: {e}")
            return False
    
    def _clear_session(self) -> None:
        """Clear existing session."""
        try:
            self.driver.delete_cookie(self.session_cookie_name)
            self.memory_updates["stats"]["is_logged_in"] = False
        except Exception as e:
            self.logger.error(f"Error clearing session: {e}")
    
    def is_logged_in(self) -> bool:
        """Check if user is logged in.
        
        Returns:
            True if logged in, False otherwise
        """
        self._last_action = "is_logged_in"
        
        try:
            # First check session cookie
            if self._validate_session_cookie():
                self.memory_updates["stats"]["is_logged_in"] = True
                return True
                
            # If no valid session, check UI elements
            # Check for user menu
            user_menu = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["user_menu"],
                timeout=2
            )
            if user_menu and user_menu.is_displayed():
                self.memory_updates["stats"]["is_logged_in"] = True
                return True
                
            # Check for login form
            login_form = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["login_form"],
                timeout=2
            )
            if login_form and login_form.is_displayed():
                self.memory_updates["stats"]["is_logged_in"] = False
                return False
                
            # Neither present - check session cookie again
            if self._validate_session_cookie():
                self.memory_updates["stats"]["is_logged_in"] = True
                return True
                
            # Not logged in
            self.memory_updates["stats"]["is_logged_in"] = False
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            self.memory_updates["stats"]["is_logged_in"] = False
            return False
    
    def _handle_login_error(self, error: Exception, context: str) -> None:
        """Handle login error.
        
        Args:
            error: The error that occurred
            context: The context where the error occurred
        """
        error_info = {
            "error": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.memory_updates["last_error"] = error_info
        self.memory_updates["errors"] = self.memory_updates.get("errors", []) + [error_info]
        
        if self.logger:
            self.logger.error(
                platform="reddit",
                status="error",
                message=f"Login error: {str(error)}",
                error=str(error),
                metadata={"context": context}
            )
    
    def login(self) -> bool:
        """Attempt to log in to Reddit.
        
        Returns:
            True if login was successful, False otherwise
        """
        if self.is_logged_in():
            return True
            
        if self.login_attempts >= self.config.max_retries:
            self._handle_login_error(
                LoginError("Maximum login attempts exceeded"),
                "max_retries"
            )
            return False
            
        try:
            # Navigate to login page
            self.driver.get(self.LOGIN_URL)
            
            # Wait for and fill username
            username_input = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["username_input"],
                timeout=10
            )
            if not username_input:
                raise NoSuchElementException("Username input not found")
            username_input.clear()
            username_input.send_keys(self.config.username)
            
            # Wait for and fill password
            password_input = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["password_input"],
                timeout=10
            )
            if not password_input:
                raise NoSuchElementException("Password input not found")
            password_input.clear()
            password_input.send_keys(self.config.password)
            
            # Click login button
            submit_button = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["submit_button"],
                timeout=10
            )
            if not submit_button:
                raise NoSuchElementException("Submit button not found")
            
            # Use retry_click for better reliability
            if not self.utils.retry_click(submit_button):
                raise ElementClickInterceptedException("Failed to click submit button")
            
            # Wait for login to complete
            time.sleep(self.config.retry_delay)
            
            # Verify login success
            if self.is_logged_in():
                self.login_attempts = 0
                self.last_login_attempt = datetime.now()
                self._save_session()
                self.memory_updates["stats"]["is_logged_in"] = True
                self.logger.info(
                    message="Login successful",
                    platform="reddit",
                    status="success"
                )
                return True
            else:
                self.login_attempts += 1
                self._handle_login_error(
                    LoginError("Login verification failed"),
                    "verification"
                )
                return False
                
        except Exception as e:
            self.login_attempts += 1
            self._handle_login_error(e, "login")
            return False
    
    def verify_session(self) -> bool:
        """Verify if current session is valid.
        
        Returns:
            True if session is valid, False otherwise
        """
        try:
            # Check session cookie
            if not self._validate_session_cookie():
                return False
                
            # Check UI elements
            user_menu = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["user_menu"],
                timeout=2
            )
            if not user_menu or not user_menu.is_displayed():
                return False
                
            return True
            
        except Exception as e:
            self._handle_login_error(e, "verify_session")
            return False
    
    def check_login_state(self) -> bool:
        """Check current login state.
        
        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check for user menu
            user_menu = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["user_menu"],
                timeout=2
            )
            if user_menu and user_menu.is_displayed():
                return True
                
            # Check for login form
            login_form = self.utils.wait_for_element(
                By.XPATH,
                self.selectors["login_form"],
                timeout=2
            )
            if login_form and login_form.is_displayed():
                return False
                
            # Check session cookie
            return self._validate_session_cookie()
            
        except Exception as e:
            self._handle_login_error(e, "check_login_state")
            return False
    
    def logout(self) -> None:
        """Perform logout."""
        self._session = None
        if self._session_file.exists():
            try:
                self._session_file.unlink()
            except Exception as e:
                logger.error(f"Error deleting session file: {str(e)}")
                
    def refresh_session(self) -> bool:
        """Refresh login session.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            LoginError: If refresh fails
        """
        self._last_action = "refresh_session"
        
        if not self._session:
            self._last_error = {"error": "No active session", "context": "no_session"}
            return False
            
        try:
            # TODO: Add actual refresh implementation
            # For now, just extend the mock session
            self._session.expires_at = datetime.now() + timedelta(hours=1)
            
            # Save session
            self._save_session()
            
            return True
            
        except Exception as e:
            self._last_error = {"error": str(e), "context": "refresh_failed"}
            logger.error(f"Session refresh failed: {str(e)}")
            return False
            
    def _save_session(self) -> None:
        """Save current session state."""
        try:
            cookies = self.driver.get_cookies()
            session = LoginSession(
                cookies=cookies,
                timestamp=datetime.now()
            )
            
            session_data = {
                'cookies': cookies,
                'timestamp': session.timestamp.isoformat()
            }
            
            with open(self._session_file, 'w') as f:
                json.dump(session_data, f)
                
            self._session = session
            self.logger.info(
                message="Session saved successfully",
                platform="reddit",
                status="success"
            )
            
        except Exception as e:
            self._handle_login_error(e, "save_session")
    
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
            if self.verify_session():
                self.logger.info(
                    message="Session loaded successfully",
                    platform="reddit",
                    status="success"
                )
                return True
                
            return False
            
        except Exception as e:
            self._handle_login_error(e, "load_session")
            return False
            
    def get_session(self) -> Optional[LoginSession]:
        """Get current session.
        
        Returns:
            Current session or None if not logged in
        """
        return self._session
        
    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests.
        
        Returns:
            Dictionary of headers
            
        Raises:
            LoginError: If not logged in
        """
        if not self.is_logged_in():
            raise LoginError("Not logged in")
            
        return {
            'Authorization': f"{self._session.token_type} {self._session.access_token}",
            'User-Agent': self.config["user_agent"]
        }
        
    def get_last_action(self) -> Optional[str]:
        """Get last action performed.
        
        Returns:
            Last action or None
        """
        return self._last_action
        
    def get_last_error(self) -> Optional[Dict[str, str]]:
        """Get last error that occurred.
        
        Returns:
            Last error or None
        """
        return self._last_error 