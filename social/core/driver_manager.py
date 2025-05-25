import os
import time
import pickle
import random
import json
import requests
from typing import List, Dict, Any, Optional, Tuple
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from dreamos.social.log_writer import logger

class ProxyManager:
    """Manages proxy rotation and validation."""
    
    def __init__(self, proxy_list: Optional[List[str]] = None):
        self.proxy_list = proxy_list or []
        self.current_proxy = None
        self.last_rotation = 0
        self.rotation_interval = 300  # 5 minutes
        
    def add_proxy(self, proxy: str) -> None:
        """Add a proxy to the rotation list."""
        if proxy not in self.proxy_list:
            self.proxy_list.append(proxy)
            logger.info(f"[Proxy] Added new proxy to rotation list")
    
    def validate_proxy(self, proxy: str) -> bool:
        """Validate if a proxy is working."""
        try:
            proxies = {
                "http": f"http://{proxy}",
                "https": f"https://{proxy}"
            }
            response = requests.get("https://api.ipify.org?format=json", 
                                 proxies=proxies, 
                                 timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"[Proxy] Validation failed for {proxy}: {str(e)}")
            return False
    
    def get_next_proxy(self) -> Optional[str]:
        """Get the next valid proxy from the rotation list."""
        if not self.proxy_list:
            return None
            
        current_time = time.time()
        if current_time - self.last_rotation < self.rotation_interval:
            return self.current_proxy
            
        # Try each proxy until we find a working one
        for _ in range(len(self.proxy_list)):
            proxy = random.choice(self.proxy_list)
            if self.validate_proxy(proxy):
                self.current_proxy = proxy
                self.last_rotation = current_time
                logger.info(f"[Proxy] Rotated to new proxy: {proxy}")
                return proxy
                
        logger.warning("[Proxy] No valid proxies found in rotation list")
        return None

class SessionState:
    """Manages session state and persistence."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_file = os.path.join(os.getcwd(), "social", "cookies", f"{session_id}_state.json")
        self.cookies_file = os.path.join(os.getcwd(), "social", "cookies", f"{session_id}_cookies.pkl")
        self.last_activity = time.time()
        self.session_data = {
            "platforms": {},
            "last_successful_login": None,
            "failed_attempts": {},
            "proxy_history": [],
            "performance_metrics": {
                "avg_load_time": 0,
                "success_rate": 0,
                "total_requests": 0
            }
        }
        self._load_state()
    
    def _load_state(self) -> None:
        """Load session state from file."""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    self.session_data = json.load(f)
                logger.info(f"[Session] Loaded state for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Session] Error loading state for session {self.session_id}: {str(e)}")
    
    def save_state(self) -> None:
        """Save session state to file."""
        try:
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(self.session_data, f, indent=2)
            logger.info(f"[Session] Saved state for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Session] Error saving state for session {self.session_id}: {str(e)}")
    
    def update_platform_state(self, platform: str, status: str, details: Dict[str, Any]) -> None:
        """Update state for a specific platform."""
        self.session_data["platforms"][platform] = {
            "status": status,
            "last_updated": time.time(),
            "details": details
        }
        self.save_state()
    
    def get_platform_state(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get state for a specific platform."""
        return self.session_data["platforms"].get(platform)
    
    def save_cookies(self, cookies: List[Dict[str, Any]]) -> None:
        """Save cookies to file."""
        try:
            os.makedirs(os.path.dirname(self.cookies_file), exist_ok=True)
            with open(self.cookies_file, 'wb') as f:
                pickle.dump(cookies, f)
            logger.info(f"[Session] Saved cookies for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Session] Error saving cookies for session {self.session_id}: {str(e)}")
    
    def load_cookies(self) -> Optional[List[Dict[str, Any]]]:
        """Load cookies from file."""
        try:
            if os.path.exists(self.cookies_file):
                with open(self.cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                logger.info(f"[Session] Loaded cookies for session {self.session_id}")
                return cookies
        except Exception as e:
            logger.error(f"[Session] Error loading cookies for session {self.session_id}: {str(e)}")
        return None

class DriverSession:
    """Manages a single Chrome driver session with profile persistence."""
    
    def __init__(self, session_id: str, proxy_rotation: bool = False, headless: bool = False):
        self.session_id = session_id
        self.proxy_rotation = proxy_rotation
        self.headless = headless
        self.driver = None
        self.profile_dir = os.path.join(os.getcwd(), "social", "profiles", session_id)
        self.proxy_manager = ProxyManager() if proxy_rotation else None
        self.session_state = SessionState(session_id)
        self.max_retries = 3
        self.retry_delay = 5
        self.wait_timeout = 30
        os.makedirs(self.profile_dir, exist_ok=True)
    
    def start_driver(self) -> None:
        """Initialize and start the Chrome driver session."""
        retry_count = 0
        while retry_count < self.max_retries:
            try:
                options = uc.ChromeOptions()
                options.add_argument(f"--user-data-dir={self.profile_dir}")
                
                if self.headless:
                    options.add_argument("--headless")
                
                if self.proxy_rotation and self.proxy_manager:
                    proxy = self.proxy_manager.get_next_proxy()
                    if proxy:
                        options.add_argument(f"--proxy-server={proxy}")
                        self.session_state.session_data["proxy_history"].append({
                            "proxy": proxy,
                            "timestamp": time.time()
                        })
                
                self.driver = uc.Chrome(
                    options=options,
                    driver_executable_path=ChromeDriverManager().install()
                )
                
                # Load saved cookies if available
                cookies = self.session_state.load_cookies()
                if cookies:
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            logger.error(f"[Driver] Error loading cookie: {str(e)}")
                
                logger.info(f"[Driver] Started session {self.session_id}")
                return
                
            except Exception as e:
                retry_count += 1
                logger.error(f"[Driver] Attempt {retry_count} failed for session {self.session_id}: {str(e)}")
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                raise
    
    def save_session(self) -> None:
        """Save current session state and cookies."""
        if self.driver:
            try:
                cookies = self.driver.get_cookies()
                self.session_state.save_cookies(cookies)
                self.session_state.save_state()
                logger.info(f"[Driver] Saved session state for {self.session_id}")
            except Exception as e:
                logger.error(f"[Driver] Error saving session state for {self.session_id}: {str(e)}")
    
    def wait_for_element(self, by: By, value: str, timeout: Optional[int] = None) -> Any:
        """Wait for an element to be present and return it."""
        timeout = timeout or self.wait_timeout
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logger.error(f"[Driver] Timeout waiting for element {value}: {str(e)}")
            raise
    
    def is_element_present(self, by: By, value: str) -> bool:
        """Check if an element is present."""
        try:
            self.driver.find_element(by, value)
            return True
        except:
            return False
    
    def execute_js(self, script: str, *args) -> Any:
        """Execute JavaScript code."""
        try:
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"[Driver] Error executing JavaScript: {str(e)}")
            raise
    
    def take_screenshot(self, filename: str) -> str:
        """Take a screenshot and save it."""
        try:
            screenshot_dir = os.path.join(os.getcwd(), "social", "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)
            filepath = os.path.join(screenshot_dir, filename)
            self.driver.save_screenshot(filepath)
            logger.info(f"[Driver] Saved screenshot to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"[Driver] Error taking screenshot: {str(e)}")
            raise
    
    def recover_session(self) -> bool:
        """Attempt to recover a failed session."""
        try:
            if self.driver:
                self.driver.quit()
            self.start_driver()
            logger.info(f"[Driver] Successfully recovered session {self.session_id}")
            return True
        except Exception as e:
            logger.error(f"[Driver] Failed to recover session {self.session_id}: {str(e)}")
            return False
    
    def shutdown_driver(self) -> None:
        """Safely shut down the Chrome driver session."""
        if self.driver:
            try:
                self.save_session()  # Save state before shutting down
                self.driver.quit()
                logger.info(f"[Driver] Shut down session {self.session_id}")
            except Exception as e:
                logger.error(f"[Driver] Error shutting down session {self.session_id}: {str(e)}")
            finally:
                self.driver = None
    
    def cleanup_profile(self) -> None:
        """Clean up the profile directory."""
        try:
            import shutil
            shutil.rmtree(self.profile_dir, ignore_errors=True)
            logger.info(f"[Driver] Cleaned up profile for session {self.session_id}")
        except Exception as e:
            logger.error(f"[Driver] Error cleaning up profile for session {self.session_id}: {str(e)}")

def get_multi_driver_sessions(
    session_ids: List[str],
    proxy_rotation: bool = False,
    headless: bool = False
) -> List[DriverSession]:
    """Create multiple driver sessions for parallel platform handling."""
    sessions = []
    for session_id in session_ids:
        try:
            session = DriverSession(session_id, proxy_rotation, headless)
            session.start_driver()
            sessions.append(session)
        except Exception as e:
            logger.error(f"[Driver] Failed to create session {session_id}: {str(e)}")
            # Clean up any sessions that were created
            for s in sessions:
                s.shutdown_driver()
                s.cleanup_profile()
            raise
    
    return sessions 