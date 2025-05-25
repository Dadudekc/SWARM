import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .platform_strategy_base import PlatformStrategy
from dreamos.social.log_writer import logger

class FacebookStrategy(PlatformStrategy):
    """Facebook platform strategy implementation."""
    
    LOGIN_URL = "https://facebook.com/login"
    HOME_URL = "https://facebook.com"
    
    def is_logged_in(self) -> bool:
        """Check if currently logged into Facebook."""
        try:
            self.driver.get(self.HOME_URL)
            time.sleep(3)  # Allow page to load
            
            # Check for login form or profile elements
            try:
                # If we can find the login form, we're not logged in
                self.driver.find_element(By.ID, "email")
                return False
            except NoSuchElementException:
                # If we can't find the login form, we're probably logged in
                return True
                
        except Exception as e:
            logger.error(f"[Facebook] Login check failed: {str(e)}")
            return False

    def login(self) -> bool:
        """Attempt to log in to Facebook."""
        try:
            self.driver.get(self.LOGIN_URL)
            time.sleep(2)  # Allow page to load
            
            # Get credentials from config
            email = self.config.get("facebook_email")
            password = self.config.get("facebook_password")
            
            if not email or not password:
                logger.error("[Facebook] Missing credentials in config")
                return False
            
            # Find and fill login form
            email_input = self.driver.find_element(By.ID, "email")
            password_input = self.driver.find_element(By.ID, "pass")
            login_button = self.driver.find_element(By.NAME, "login")
            
            email_input.send_keys(email)
            password_input.send_keys(password)
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Verify login success
            if self.is_logged_in():
                logger.info("[Facebook] Login successful")
                return True
            else:
                logger.error("[Facebook] Login failed - credentials may be invalid")
                return False
                
        except Exception as e:
            logger.error(f"[Facebook] Login error: {str(e)}")
            return False

    def post(self, content: str) -> bool:
        """Post content to Facebook."""
        try:
            # Navigate to home page
            self.driver.get(self.HOME_URL)
            time.sleep(5)  # Allow page to load
            
            # Find and click the post creation box
            post_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Create a post']"))
            )
            post_box.click()
            time.sleep(3)
            
            # Find the content input area
            active_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']//div[@contenteditable='true']"))
            )
            active_box.send_keys(content)
            time.sleep(2)
            
            # Find and click the Post button
            post_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//div[@aria-label='Post']"))
            )
            post_button.click()
            
            # Wait for post to complete
            time.sleep(5)
            
            logger.info(f"[Facebook] Post successful: {content}")
            return True
            
        except TimeoutException:
            logger.error("[Facebook] Post failed - timeout waiting for elements")
            return False
        except Exception as e:
            logger.error(f"[Facebook] Post error: {str(e)}")
            return False 