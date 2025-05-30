from typing import Optional, Dict, Any
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

class LoginHandler:
    """Handles all login-related operations for Reddit."""
    
    def __init__(self, driver, config: dict, memory_update: Optional[Dict[str, Any]] = None):
        self.driver = driver
        self.config = config
        self.memory_update = memory_update or {}
        
        # Reddit-specific selectors
        self.selectors = {
            "login_button": "//button[contains(text(), 'Log In')]",
            "username_input": "//input[@name='username']",
            "password_input": "//input[@name='password']",
            "submit_button": "//button[@type='submit']",
            "login_verification": "//div[contains(@class, 'UserMenu')]"
        }
        
    def login(self, username: str, password: str) -> bool:
        """Log in to Reddit.
        
        Args:
            username: Reddit username
            password: Reddit password
            
        Returns:
            bool: True if login was successful, False otherwise
        """
        try:
            # Click login button
            login_button = self.driver.find_element(By.XPATH, self.selectors["login_button"])
            login_button.click()
            
            # Enter credentials
            username_input = self.driver.find_element(By.XPATH, self.selectors["username_input"])
            username_input.send_keys(username)
            
            password_input = self.driver.find_element(By.XPATH, self.selectors["password_input"])
            password_input.send_keys(password)
            
            # Submit login
            submit_button = self.driver.find_element(By.XPATH, self.selectors["submit_button"])
            submit_button.click()
            
            # Verify login success
            return self._verify_login_success()
            
        except (TimeoutException, ElementClickInterceptedException) as e:
            self.memory_update["last_error"] = str(e)
            return False
            
    def _verify_login_success(self) -> bool:
        """Verify that the login was successful."""
        try:
            self.driver.find_element(By.XPATH, self.selectors["login_verification"])
            return True
        except TimeoutException:
            return False 