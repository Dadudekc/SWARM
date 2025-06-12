"""
Main bridge service implementation.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import undetected_chromedriver as uc
try:
    import win32gui
except ImportError:  # pragma: no cover - Windows only dependency
    win32gui = None
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    NoSuchWindowException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
import yaml

from dreamos.bridge.models.request import BridgeRequest
from dreamos.bridge.models.health import BridgeHealth
from ..utils import HybridResponseHandler
from .constants import (
    CHATGPT_URL,
    GPT_URL,
    PROFILE_DIR,
    COOKIE_FILE,
    CONTENT_LOG_DIR,
    CHAT_INPUT_SELECTORS,
    SEND_BUTTON_SELECTORS,
    LOGIN_BUTTON_SELECTORS
)

# Configure logging
logger = logging.getLogger('bridge')

class ChatGPTBridge:
    """Main bridge service for ChatGPT integration."""
    
    def __init__(self, config_path: str):
        """Initialize bridge service."""
        self.config = self._load_config(config_path)
        self._validate_config()
        
        # Initialize components
        self.driver: Optional[uc.Chrome] = None
        self.window_handle: Optional[int] = None
        self.requests: List[BridgeRequest] = []
        self.health = BridgeHealth(
            is_healthy=True,
            last_check=datetime.now(),
            error_count=0,
            last_error=None,
            session_active=False,
            message_count=0
        )
        
        # Set up paths
        self.queue_file = os.path.join('runtime', 'bridge_inbox', 'requests.json')
        self.health_file = os.path.join('runtime', 'bridge_inbox', 'health.json')
        os.makedirs(os.path.dirname(self.queue_file), exist_ok=True)
        
        # Create hybrid response handler
        self.hybrid_handler = HybridResponseHandler()
        
        self._running = False
        self._process_task: Optional[asyncio.Task] = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        logger.info(f"Loading config from {config_path}")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
            
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info("Config loaded successfully")
            return config
            
    def _validate_config(self) -> None:
        """Validate configuration values."""
        logger.info("Validating configuration...")
        required = ['window_title', 'page_load_wait', 
                   'response_wait', 'paste_delay', 'max_retries']
        missing = [field for field in required if field not in self.config]
        if missing:
            raise ValueError(f"Missing required config fields: {', '.join(missing)}")
            
        logger.info("Configuration validation complete")
        
    async def start(self) -> None:
        """Start bridge service."""
        if self._running:
            logger.warning("Bridge service already running")
            return
            
        self._running = True
        await self._launch_browser()
        self._process_task = asyncio.create_task(self._process_requests())
        logger.info("Bridge service started")
        
    async def stop(self) -> None:
        """Stop bridge service."""
        if not self._running:
            logger.warning("Bridge service not running")
            return
            
        self._running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
                
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {e}")
                
        logger.info("Bridge service stopped")
        
    async def _launch_browser(self) -> None:
        """Launch Chrome browser with undetected-chromedriver."""
        logger.info("Launching browser...")
        
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # Set up user data directory
        options.add_argument(f'--user-data-dir={PROFILE_DIR}')
        
        try:
            self.driver = uc.Chrome(
                driver_executable_path=ChromeDriverManager().install(),
                options=options
            )
            logger.info("Browser launched successfully")
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            raise
            
    def _find_chat_input(self, driver) -> Optional[Any]:
        """Find the chat input element."""
        for selector in CHAT_INPUT_SELECTORS:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except (NoSuchElementException, ElementNotInteractableException):
                continue
        return None
        
    def _find_send_button(self, driver) -> Optional[Any]:
        """Find the send button element."""
        for selector in SEND_BUTTON_SELECTORS:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except (NoSuchElementException, ElementNotInteractableException):
                continue
        return None
        
    def _find_login_button(self, driver) -> Optional[Any]:
        """Find the login button element."""
        for selector in LOGIN_BUTTON_SELECTORS:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed() and element.is_enabled():
                    return element
            except (NoSuchElementException, ElementNotInteractableException):
                continue
        return None
        
    async def send_message(self, message: str) -> str:
        """Send a message to ChatGPT and wait for response."""
        if not self.driver:
            raise RuntimeError("Browser not initialized")
            
        try:
            # Find and interact with chat input
            chat_input = self._find_chat_input(self.driver)
            if not chat_input:
                raise RuntimeError("Could not find chat input")
                
            # Clear and send message
            chat_input.clear()
            chat_input.send_keys(message)
            
            # Find and click send button
            send_button = self._find_send_button(self.driver)
            if not send_button:
                raise RuntimeError("Could not find send button")
                
            send_button.click()
            
            # Wait for response
            await asyncio.sleep(self.config['response_wait'])
            
            # Get response
            response = self.driver.find_element(By.CSS_SELECTOR, 'div[data-message-author-role="assistant"]').text
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
            
    async def _process_requests(self) -> None:
        """Process queued requests."""
        while self._running:
            try:
                if os.path.exists(self.queue_file):
                    with open(self.queue_file, 'r') as f:
                        requests = json.load(f)
                        
                    for request_data in requests:
                        request = BridgeRequest(**request_data)
                        try:
                            response = await self.send_message(request.message)
                            request.response = response
                            request.status = 'completed'
                        except Exception as e:
                            request.error = str(e)
                            request.status = 'failed'
                            
                    self._save_requests()
                    
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error processing requests: {e}")
                await asyncio.sleep(5)
                
    def _save_requests(self) -> None:
        """Save request queue to file."""
        with open(self.queue_file, 'w') as f:
            json.dump([vars(r) for r in self.requests], f)
            
    def _save_health(self) -> None:
        """Save health status to file."""
        with open(self.health_file, 'w') as f:
            json.dump(vars(self.health), f)
            
    def _is_logged_in(self) -> bool:
        """Check if user is logged in to ChatGPT."""
        try:
            return bool(self._find_chat_input(self.driver))
        except Exception:
            return False
            
    async def _wait_for_chat_input(self, timeout: int = 30) -> None:
        """Wait for chat input to be available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_logged_in():
                return
            await asyncio.sleep(1)
        raise TimeoutError("Chat input not found within timeout")
        
    async def _navigate_to_gpt(self, max_retries: int = 3) -> bool:
        """Navigate to ChatGPT URL with retries."""
        for attempt in range(max_retries):
            try:
                self.driver.get(GPT_URL)
                await self._wait_for_chat_input()
                return True
            except Exception as e:
                logger.error(f"Navigation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(2)
        return False 