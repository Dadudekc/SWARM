"""
ChatGPT Bridge

Consolidated implementation of the ChatGPT bridge service.
"""

import asyncio
import json
import logging
import os
import re
import shutil
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pyautogui
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bridge')

# Constants
CHATGPT_URL = "https://chat.openai.com/"
GPT_URL = "https://chatgpt.com/g/g-6817f1a5d2e88191948898629f7e8d9b-protocol-commander-thea"
CURRENT_DIR = os.path.abspath(os.getcwd())
PROFILE_DIR = os.path.join(CURRENT_DIR, "runtime", "chrome_profile")
COOKIE_FILE = os.path.join(CURRENT_DIR, "runtime", "cookies", "openai.pkl")
CONTENT_LOG_DIR = os.path.join(CURRENT_DIR, "runtime", "chat_logs")

# Ensure directories exist
os.makedirs(PROFILE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
os.makedirs(CONTENT_LOG_DIR, exist_ok=True)

# Selectors for ChatGPT UI elements
CHAT_INPUT_SELECTORS = [
    'p[data-placeholder="Ask anything"]',  # New primary selector
    'textarea[data-id="chat-input"]',      # Older selector
    'textarea[placeholder="Send a message"]',
    'textarea[aria-label="Chat input"]',
]

SEND_BUTTON_SELECTORS = [
    'button[data-testid="send-button"]',     # Primary test ID
    'button[class*="send"]',                 # Class containing 'send'
    'button[aria-label*="Send"]',            # Aria label containing 'Send'
    "//button[.//span[text()='Send message']]", # XPath for specific text
]

LOGIN_BUTTON_SELECTORS = [
    'button[data-testid="welcome-login-button"]',  # Primary test ID
    'button.btn-primary[data-testid*="login"]',    # Class + test ID
    'button:has(div:contains("Log in"))',         # Contains text
    "//button[.//div[contains(text(), 'Log in')]]", # XPath for text
]

@dataclass
class BridgeRequest:
    """A request to be processed by the bridge."""
    id: str
    message: str
    timestamp: datetime
    status: str
    response: Optional[str] = None
    error: Optional[str] = None

@dataclass
class BridgeHealth:
    """Health status information."""
    is_healthy: bool
    last_check: datetime
    error_count: int
    last_error: Optional[str]
    session_active: bool
    message_count: int

class HybridResponseHandler:
    """Parses hybrid responses containing both text and structured data."""
    
    def parse_hybrid_response(self, raw_response: str) -> Tuple[str, dict]:
        """Extract text and structured JSON data from a hybrid response."""
        logger.info("Parsing hybrid response for narrative text and MEMORY_UPDATE JSON")
        
        # Regex to capture JSON block between ```json and ```
        json_pattern = r"""```json(.*?)```"""
        match = re.search(json_pattern, raw_response, re.DOTALL)

        if match:
            json_content = match.group(1).strip()
            try:
                memory_update = json.loads(json_content)
                logger.info("Successfully parsed MEMORY_UPDATE JSON")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                memory_update = {}
        else:
            logger.info("No JSON block found in the response")
            memory_update = {}

        # Remove the JSON block from the raw response to extract pure narrative text
        text_part = re.sub(json_pattern, "", raw_response, flags=re.DOTALL).strip()

        return text_part, memory_update

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
        logger.info("Starting bridge service...")
        if self._running:
            logger.info("Bridge service already running")
            return
            
        try:
            await self._launch_browser()
            self._running = True
            self._process_task = asyncio.create_task(self._process_requests())
            logger.info("Bridge service started successfully")
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            await self.stop()
            raise
            
    async def stop(self) -> None:
        """Stop bridge service."""
        if not self._running:
            return
            
        self._running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
                
        if self.driver:
            self.driver.quit()
            self.driver = None
            
        self._save_health()
        logger.info("Bridge service stopped")
        
    async def _launch_browser(self) -> None:
        """Launch Chrome browser with retry logic."""
        for attempt in range(self.config['max_retries']):
            try:
                logger.info(f"Launch attempt {attempt + 1} of {self.config['max_retries']}")
                options = uc.ChromeOptions()
                
                # Set explicit Chrome binary location
                chrome_paths = [
                    "C:/Program Files/Google/Chrome/Application/chrome.exe",
                    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
                    os.path.expanduser("~/AppData/Local/Google/Chrome/Application/chrome.exe")
                ]
                
                chrome_path = None
                for path in chrome_paths:
                    if os.path.exists(path):
                        chrome_path = path
                        logger.info(f"Found Chrome at: {chrome_path}")
                        break
                
                if not chrome_path:
                    raise RuntimeError("Chrome not found. Please install Chrome or set correct path in config.")
                
                options.binary_location = chrome_path
                
                # Add required arguments
                logger.info(f"Using Chrome profile directory: {PROFILE_DIR}")
                options.add_argument(f"--user-data-dir={PROFILE_DIR}")
                options.add_argument('--start-maximized')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--dns-prefetch-disable')
                options.add_argument('--disable-extensions')
                options.add_argument('--disable-software-rasterizer')
                options.add_argument('--disable-features=VizDisplayCompositor')
                
                logger.info("Launching Chrome with options...")
                try:
                    # Use undetected_chromedriver for better anti-bot evasion
                    self.driver = uc.Chrome(options=options)
                    logger.info("Chrome launched successfully")
                except Exception as e:
                    logger.error(f"Failed to launch Chrome: {str(e)}")
                    raise
                
                self.driver.set_page_load_timeout(self.config['page_load_wait'])
                
                try:
                    logger.info("Navigating to ChatGPT...")
                    self.driver.get(CHATGPT_URL)
                    logger.info("Navigated to ChatGPT")
                except TimeoutException:
                    logger.warning("Page load timeout, retrying...")
                    continue
                except Exception as e:
                    logger.error(f"Navigation error: {str(e)}")
                    raise
                
                try:
                    logger.info("Waiting for page to load...")
                    WebDriverWait(self.driver, self.config['page_load_wait']).until(
                        EC.presence_of_element_located((By.TAG_NAME, 'body'))
                    )
                    logger.info("Page loaded successfully")
                    
                    # Check for login button and click if found
                    login_button = self._find_login_button(self.driver)
                    if login_button:
                        logger.info("Login button found, attempting to click...")
                        try:
                            # Try JavaScript click first
                            self.driver.execute_script("arguments[0].click();", login_button)
                            logger.info("Clicked login button using JavaScript")
                            
                            # Wait for login page to load
                            logger.info("Waiting for login page to load...")
                            await asyncio.sleep(3)
                            
                            # Verify we're on the login page
                            current_url = self.driver.current_url
                            logger.info(f"Current URL after login click: {current_url}")
                            
                            if "auth" in current_url.lower():
                                logger.info("Successfully navigated to login page")
                            else:
                                logger.warning("May not have reached login page, current URL: {current_url}")
                                
                        except Exception as e:
                            logger.error(f"Error clicking login button: {e}")
                            # Try regular click as fallback
                            try:
                                login_button.click()
                                logger.info("Clicked login button using regular click")
                                await asyncio.sleep(3)
                            except Exception as e2:
                                logger.error(f"Fallback click also failed: {e2}")
                    else:
                        logger.info("No login button found - may be already logged in")
                        
                    # Check if we're logged in by looking for the chat input
                    if self._is_logged_in():
                        logger.info("Successfully logged in, navigating to GPT URL...")
                        if await self._navigate_to_gpt():
                            logger.info("Successfully navigated to GPT and verified chat interface")
                        else:
                            raise RuntimeError("Failed to navigate to GPT URL")
                    else:
                        logger.warning("Not logged in after login attempt")
                        
                except TimeoutException:
                    logger.warning("Element wait timeout, retrying...")
                    continue
                except Exception as e:
                    logger.error(f"Page load error: {str(e)}")
                    raise
                
                if win32gui:
                    self.window_handle = win32gui.FindWindow(None, self.config['window_title'])
                    if self.window_handle:
                        win32gui.SetForegroundWindow(self.window_handle)
                        logger.info("Focused Cursor window")
                    
                self.health.session_active = True
                self._save_health()
                return
                
            except WebDriverException as e:
                logger.error(f"Browser error on attempt {attempt + 1}: {e}")
                if attempt == self.config['max_retries'] - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt == self.config['max_retries'] - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
    def _find_chat_input(self, driver) -> Optional[Any]:
        """Find the chat input field using multiple possible selectors."""
        for selector in CHAT_INPUT_SELECTORS:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    element = driver.find_element(By.XPATH, selector)
                else:
                    # CSS selector
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                return element
            except Exception:
                continue
        return None
        
    def _find_send_button(self, driver) -> Optional[Any]:
        """Find the send button using multiple possible selectors."""
        for selector in SEND_BUTTON_SELECTORS:
            try:
                if selector.startswith("//"):
                    # XPath selector
                    element = driver.find_element(By.XPATH, selector)
                else:
                    # CSS selector
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                return element
            except Exception:
                continue
        return None
        
    def _find_login_button(self, driver) -> Optional[Any]:
        """Find the login button using multiple possible selectors."""
        logger.info("Searching for login button...")
        for selector in LOGIN_BUTTON_SELECTORS:
            try:
                logger.debug(f"Trying selector: {selector}")
                if selector.startswith("//"):
                    # XPath selector
                    element = driver.find_element(By.XPATH, selector)
                else:
                    # CSS selector
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    
                if element.is_displayed() and element.is_enabled():
                    logger.info(f"Found login button using selector: {selector}")
                    return element
                else:
                    logger.debug(f"Found element but not clickable: {selector}")
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {str(e)}")
                continue
                
        logger.info("No login button found with any selector")
        return None
        
    async def send_message(self, message: str) -> str:
        """Send message to ChatGPT."""
        request = BridgeRequest(
            id=datetime.now().strftime('%Y%m%d_%H%M%S_%f'),
            message=message,
            timestamp=datetime.now(),
            status='pending'
        )
        self.requests.append(request)
        self._save_requests()
        
        try:
            if not self.driver:
                await self._launch_browser()
                
            # Find and interact with the input field
            input_field = self._find_chat_input(self.driver)
            if not input_field:
                raise RuntimeError("Could not find chat input field")
                
            try:
                # Focus and clear the input field
                input_field.click()
                time.sleep(0.5)
                
                # Enter text (in chunks if necessary)
                chunk_size = 1000  # Send text in chunks to avoid issues with very long prompts
                for i in range(0, len(message), chunk_size):
                    chunk = message[i:i + chunk_size]
                    input_field.send_keys(chunk)
                    time.sleep(0.3)
                    
                logger.info("Text entered successfully")
                
                # Find and click send button or use Enter key
                send_button = self._find_send_button(self.driver)
                if send_button and send_button.is_enabled():
                    send_button.click()
                    logger.info("Clicked send button")
                else:
                    # Fallback to Enter key
                    input_field.send_keys(Keys.RETURN)
                    logger.info("Used Enter key to send")
                    
                # Wait for response
                await asyncio.sleep(self.config['response_wait'])
                
                # Get response
                response_elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    'div[data-message-author-role="assistant"]'
                )
                
                if not response_elements:
                    raise RuntimeError("No response received")
                    
                response = response_elements[-1].text
                request.status = 'completed'
                request.response = response
                self.health.message_count += 1
                self._save_requests()
                self._save_health()
                return response
                
            except ElementNotInteractableException:
                raise RuntimeError("Chat input is not interactable")
            except StaleElementReferenceException:
                raise RuntimeError("Element reference is stale")
                
        except Exception as e:
            request.status = 'failed'
            request.error = str(e)
            self.health.error_count += 1
            self.health.last_error = str(e)
            self._save_requests()
            self._save_health()
            raise
            
    async def _process_requests(self) -> None:
        """Process pending requests."""
        while self._running:
            try:
                pending = [r for r in self.requests if r.status == 'pending']
                for request in pending:
                    try:
                        await self.send_message(request.message)
                    except Exception as e:
                        logger.error(f"Error processing request {request.id}: {e}")
                        
                self.requests = [r for r in self.requests if r.status == 'pending']
                self._save_requests()
                
                if not self.driver:
                    await self._launch_browser()
                    
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in request processing loop: {e}")
                await asyncio.sleep(5)
                
    def _save_requests(self) -> None:
        """Save requests to file."""
        try:
            with open(self.queue_file, 'w') as f:
                json.dump([{
                    'id': r.id,
                    'message': r.message,
                    'timestamp': r.timestamp.isoformat(),
                    'status': r.status,
                    'response': r.response,
                    'error': r.error
                } for r in self.requests], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save requests: {e}")
            
    def _save_health(self) -> None:
        """Save health status to file."""
        try:
            with open(self.health_file, 'w') as f:
                json.dump({
                    'is_healthy': self.health.is_healthy,
                    'last_check': self.health.last_check.isoformat(),
                    'error_count': self.health.error_count,
                    'last_error': self.health.last_error,
                    'session_active': self.health.session_active,
                    'message_count': self.health.message_count
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health status: {e}")

    def _is_logged_in(self) -> bool:
        """Check if we're logged in by looking for the chat input."""
        try:
            input_field = self._find_chat_input(self.driver)
            return input_field is not None and input_field.is_displayed()
        except Exception as e:
            logger.debug(f"Error checking login status: {e}")
            return False

    async def _wait_for_chat_input(self, timeout: int = 30) -> None:
        """Wait for the chat input to be available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._is_logged_in():
                return
            await asyncio.sleep(1)
        raise TimeoutException("Timed out waiting for chat input")

    async def _navigate_to_gpt(self, max_retries: int = 3) -> bool:
        """Navigate to the GPT URL with retry logic."""
        for attempt in range(max_retries):
            try:
                logger.info(f"Navigating to GPT URL (attempt {attempt + 1}/{max_retries})...")
                self.driver.get(GPT_URL)
                logger.info("Navigated to GPT URL")
                
                # Wait for the chat input to be available
                await self._wait_for_chat_input()
                logger.info("Chat interface is ready")
                return True
                
            except TimeoutException:
                logger.warning(f"Timeout waiting for chat interface (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
            except Exception as e:
                logger.error(f"Error navigating to GPT URL: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                continue
                
        logger.error("Failed to navigate to GPT URL after all attempts")
        return False

async def main() -> None:
    """Main entry point."""
    logger.info("Initializing bridge service...")
    
    try:
        bridge = ChatGPTBridge('config/chatgpt_bridge.yaml')
        logger.info("Bridge instance created")
        
        await bridge.start()
        logger.info("Bridge service running, waiting for requests...")
        
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        if 'bridge' in locals():
            await bridge.stop()

if __name__ == '__main__':
    asyncio.run(main()) 
