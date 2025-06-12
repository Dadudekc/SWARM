"""
Handles the login process for multiple social media platforms using Selenium.
Leverages a persistent Chrome profile, stored cookies, and manual fallback
(for captchas or special login flows).

Supported Platforms:
  - LinkedIn
  - Twitter (X)
  - Facebook
  - Instagram
  - Reddit
  - Stocktwits
"""

import os
import time
import pickle
from typing import Optional, Dict, Any, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.file_ops import ensure_dir
from dreamos.social.utils.log_manager import LogManager
from dreamos.social.utils.social_common import SocialConfig
from dreamos.core.security.session_manager import SessionManager

logger = get_logger(__name__)

class LoginResult:
    """Result of a login attempt."""
    def __init__(self, success: bool, session_data: Optional[dict] = None, error: Optional[str] = None):
        self.success = success
        self.session_data = session_data or {}
        self.error = error

class PlatformLoginManager:
    """Manages social media platform logins with persistent sessions."""
    
    def __init__(self, config: Optional[SocialConfig] = None, session_manager: Optional[SessionManager] = None):
        self.config = config or SocialConfig()
        self.session_manager = session_manager or SessionManager()
        self.cookie_dir = ensure_dir(os.path.join(self.config.get("paths", "data"), "cookies"))
        self.profile_path = self.config.get("paths", "chrome_profile")
        self.credentials = self._load_credentials()
        self.driver = None
        self.max_attempts = 3
        self.platform_handlers = {
            "reddit": self.login_reddit,
            "twitter": self.login_twitter,
            "facebook": self.login_facebook,
            "instagram": self.login_instagram,
            "linkedin": self.login_linkedin,
            "stocktwits": self.login_stocktwits
        }

    def _load_credentials(self) -> Dict[str, Dict[str, str]]:
        """Load credentials from config."""
        return {
            "linkedin": {
                "email": self.config.get("credentials", "linkedin_email"),
                "password": self.config.get("credentials", "linkedin_password")
            },
            "twitter": {
                "email": self.config.get("credentials", "twitter_email"),
                "password": self.config.get("credentials", "twitter_password")
            },
            "facebook": {
                "email": self.config.get("credentials", "facebook_email"),
                "password": self.config.get("credentials", "facebook_password")
            },
            "instagram": {
                "email": self.config.get("credentials", "instagram_email"),
                "password": self.config.get("credentials", "instagram_password")
            },
            "reddit": {
                "email": self.config.get("credentials", "reddit_username"),
                "password": self.config.get("credentials", "reddit_password")
            },
            "stocktwits": {
                "email": self.config.get("credentials", "stocktwits_username"),
                "password": self.config.get("credentials", "stocktwits_password")
            }
        }

    def get_driver(self) -> webdriver.Chrome:
        """Initialize and return a Chrome driver with persistent profile."""
        if self.driver is None:
            options = Options()
            options.add_argument("--start-maximized")
            options.add_argument(f"--user-data-dir={self.profile_path}")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            logger.info("Chrome driver initialized with profile: %s", self.profile_path)
        return self.driver

    def load_cookies(self, platform: str) -> None:
        """Load saved cookies for the given platform."""
        cookie_path = os.path.join(self.cookie_dir, f"{platform}.pkl")
        if os.path.exists(cookie_path):
            with open(cookie_path, "rb") as file:
                cookies = pickle.load(file)
                for cookie in cookies:
                    cookie.pop("sameSite", None)
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception as e:
                        logger.error("Error adding cookie for %s: %s", platform, e)
            logger.info("Loaded cookies for %s", platform)
        else:
            logger.info("No cookies found for %s", platform)

    def save_cookies(self, platform: str) -> None:
        """Save current session cookies."""
        cookie_path = os.path.join(self.cookie_dir, f"{platform}.pkl")
        with open(cookie_path, "wb") as file:
            pickle.dump(self.driver.get_cookies(), file)
        logger.info("Saved cookies for %s", platform)

    def wait_for_manual_login(self, check_func: Callable[[webdriver.Chrome], bool], platform: str) -> bool:
        """Handle manual login with user interaction."""
        attempts = 0
        while attempts < self.max_attempts:
            input(f"Please complete the login for {platform} in the browser, then press Enter when done...")
            if check_func(self.driver):
                logger.info("%s login detected", platform.capitalize())
                self.save_cookies(platform)
                return True
            else:
                logger.warning("%s login not detected. Try again", platform.capitalize())
                attempts += 1
        logger.error("Maximum attempts reached for %s", platform)
        return False

    def login(self, platform: str, credentials: Optional[Dict[str, str]] = None) -> LoginResult:
        """Main login method that routes to platform-specific handlers."""
        platform = platform.lower()
        handler = self.platform_handlers.get(platform)
        if not handler:
            logger.error("Unsupported platform: %s", platform)
            return LoginResult(False, error="Unsupported platform")
        
        try:
            if credentials:
                self.credentials[platform] = credentials
            success = handler()
            if success:
                session_data = {
                    "cookies": self.driver.get_cookies(),
                    "platform": platform,
                    "timestamp": time.time()
                }
                self.session_manager.store_session(platform, session_data)
                return LoginResult(True, session_data=session_data)
            return LoginResult(False, error="Login failed")
        except Exception as e:
            logger.exception("Error during %s login", platform)
            return LoginResult(False, error=str(e))

    def login_linkedin(self) -> bool:
        """Handle LinkedIn login."""
        platform = "linkedin"
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        self.load_cookies(platform)
        self.driver.refresh()
        time.sleep(3)

        if "feed" in self.driver.current_url:
            logger.info("Already logged into LinkedIn")
            return True

        creds = self.credentials.get(platform, {})
        if creds.get("email") and creds.get("password"):
            try:
                self.driver.find_element(By.ID, "username").send_keys(creds["email"])
                self.driver.find_element(By.ID, "password").send_keys(creds["password"], Keys.RETURN)
            except Exception as e:
                logger.error("Automatic login error for %s: %s", platform, e)

        return self.wait_for_manual_login(lambda d: "feed" in d.current_url, platform)

    def login_twitter(self) -> bool:
        """Handle Twitter login."""
        platform = "twitter"
        self.driver.get("https://twitter.com/login")
        time.sleep(5)

        self.load_cookies(platform)
        self.driver.refresh()
        time.sleep(5)

        if "home" in self.driver.current_url:
            logger.info("Already logged into Twitter")
            return True

        creds = self.credentials.get(platform, {})
        if creds.get("email") and creds.get("password"):
            try:
                email_field = self.driver.find_element(By.NAME, "text")
                email_field.send_keys(creds["email"], Keys.RETURN)
                time.sleep(3)
                try:
                    self.driver.find_element(By.XPATH, "//span[contains(text(),'Next')]").click()
                    time.sleep(3)
                except Exception:
                    pass
                password_field = self.driver.find_element(By.NAME, "password")
                password_field.send_keys(creds["password"], Keys.RETURN)
            except Exception as e:
                logger.error("Automatic login error for %s: %s", platform, e)

        return self.wait_for_manual_login(lambda d: "home" in d.current_url, platform)

    def login_facebook(self) -> bool:
        """Handle Facebook login."""
        platform = "facebook"
        self.driver.get("https://www.facebook.com/login/")
        time.sleep(3)

        self.load_cookies(platform)
        self.driver.refresh()
        time.sleep(3)

        def fb_logged_in(d):
            try:
                d.find_element(By.XPATH, "//div[contains(@aria-label, 'Create a post')]")
                return True
            except:
                return False

        if fb_logged_in(self.driver):
            logger.info("Already logged into Facebook")
            return True

        creds = self.credentials.get(platform, {})
        if creds.get("email") and creds.get("password"):
            try:
                self.driver.find_element(By.ID, "email").send_keys(creds["email"])
                self.driver.find_element(By.ID, "pass").send_keys(creds["password"], Keys.RETURN)
            except Exception as e:
                logger.error("Automatic login error for %s: %s", platform, e)

        return self.wait_for_manual_login(fb_logged_in, platform)

    def is_instagram_logged_in(self) -> bool:
        """Check Instagram login status."""
        try:
            self.driver.find_element(By.XPATH, "//div[contains(@aria-label, 'Profile')]")
            return True
        except:
            pass

        if "accounts/onetap" in self.driver.current_url:
            return True

        self.driver.get("https://www.instagram.com/direct/inbox/")
        time.sleep(5)
        
        if "login" in self.driver.current_url:
            logger.warning("Instagram login check failed: Redirected to login page")
            return False

        logger.info("Confirmed Instagram login via Direct Messages")
        return True

    def login_instagram(self) -> bool:
        """Handle Instagram login."""
        platform = "instagram"
        self.driver.get("https://www.instagram.com/accounts/login/")
        time.sleep(5)

        creds = self.credentials.get(platform, {})
        if not creds.get("email") or not creds.get("password"):
            logger.warning("No Instagram credentials provided")
            return False

        self.load_cookies(platform)
        self.driver.refresh()
        time.sleep(5)

        if self.is_instagram_logged_in():
            logger.info("Already logged into Instagram")
            return True

        try:
            username_field = self.driver.find_element(By.NAME, "username")
            password_field = self.driver.find_element(By.NAME, "password")
            username_field.send_keys(creds["email"])
            password_field.send_keys(creds["password"], Keys.RETURN)
            time.sleep(5)
        except Exception as e:
            logger.error("Automatic login error for Instagram: %s", e)

        if not self.is_instagram_logged_in():
            logger.warning("Instagram login failed. Manual login required")
            return self.wait_for_manual_login(self.is_instagram_logged_in, platform)

        return True

    def login_reddit(self) -> bool:
        """Handle Reddit login."""
        platform = "reddit"
        self.driver.get("https://www.reddit.com/login/")
        time.sleep(5)

        self.load_cookies(platform)
        self.driver.refresh()
        time.sleep(5)

        if "reddit.com" in self.driver.current_url and "login" not in self.driver.current_url:
            logger.info("Already logged into Reddit")
            return True

        creds = self.credentials.get(platform, {})
        if creds.get("email") and creds.get("password"):
            try:
                time.sleep(3)
                username_field = self.driver.find_element(By.ID, "loginUsername")
                password_field = self.driver.find_element(By.ID, "loginPassword")
                username_field.send_keys(creds["email"])
                password_field.send_keys(creds["password"], Keys.RETURN)
            except Exception as e:
                logger.error("Automatic login error for %s: %s", platform, e)

        return self.wait_for_manual_login(
            lambda d: ("reddit.com" in d.current_url and "login" not in d.current_url),
            platform
        )

    def login_stocktwits(self) -> bool:
        """Handle Stocktwits login."""
        platform = "stocktwits"
        self.driver.get("https://stocktwits.com/signin")
        time.sleep(5)

        self.load_cookies(platform)
        self.driver.refresh()
        time.sleep(5)

        def is_logged_in(d):
            d.get("https://stocktwits.com/settings/preferences")
            time.sleep(3)
            return "preferences" in d.current_url.lower()

        if is_logged_in(self.driver):
            logger.info("Already logged into Stocktwits")
            return True

        creds = self.credentials.get(platform, {})
        if creds.get("email") and creds.get("password"):
            try:
                username_field = self.driver.find_element(By.XPATH, "//input[@name='username' or contains(@id, 'email')]")
                password_field = self.driver.find_element(By.XPATH, "//input[@name='password' or contains(@id, 'password')]")
                login_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Log In')]")

                username_field.send_keys(creds["email"])
                password_field.send_keys(creds["password"])
                login_button.click()
                time.sleep(5)
            except Exception as e:
                logger.error("Automatic login error for %s: %s", platform, e)

        if not is_logged_in(self.driver):
            logger.warning("Stocktwits login failed. Manual login required")
            return self.wait_for_manual_login(is_logged_in, platform)

        return True

    def run_all_logins(self) -> Dict[str, bool]:
        """Run login sequence for all platforms."""
        results = {}
        self.driver = self.get_driver()
        
        login_functions = [
            (self.login_stocktwits, "Stocktwits"),
            (self.login_twitter, "Twitter"),
            (self.login_facebook, "Facebook"),
            (self.login_instagram, "Instagram"),
            (self.login_reddit, "Reddit"),
            (self.login_linkedin, "LinkedIn")
        ]
        
        for login_fn, platform in login_functions:
            try:
                results[platform] = login_fn()
            except Exception as e:
                logger.error("Error during %s login: %s", platform, e)
                results[platform] = False
        
        logger.info("All logins attempted. Results: %s", results)
        return results

    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
