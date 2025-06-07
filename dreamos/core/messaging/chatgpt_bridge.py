"""
ChatGPT Bridge Integration
-------------------------
Provides integration between Dream.OS CellPhone system and ChatGPT via undetected-chromedriver.
"""

import time
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import threading
import queue
import asyncio
import undetected_chromedriver as uc
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
    ElementClickInterceptedException
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

if not os.environ.get("SWARM_SKIP_BRIDGE"):
    import pyautogui
    import pygetwindow as gw
else:
    pyautogui = None
    gw = None

from ..log_manager import LogManager
from .cell_phone import CellPhone

# Constants
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2
DEFAULT_SESSION_TIMEOUT = 3600  # 1 hour
PENDING_FILE = Path("runtime/bridge_inbox/pending_requests.json")

class ChatGPTBridge:
    """Manages communication between Dream.OS agents and ChatGPT."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ChatGPT bridge."""
        self.config = config or {}
        self.logger = LogManager()
        self.cell_phone = CellPhone()
        
        # Default configuration
        self.user_data_dir = self.config.get(
            "user_data_dir",
            str(Path.home() / "AppData/Local/Google/Chrome/User Data")
        )
        self.cursor_window_title = self.config.get("cursor_window_title", "Cursor – agent")
        self.page_load_wait = self.config.get("page_load_wait", 10)
        self.response_wait = self.config.get("response_wait", 5)
        self.paste_delay = self.config.get("paste_delay", 0.5)
        self.max_retries = self.config.get("max_retries", DEFAULT_MAX_RETRIES)
        self.backoff_factor = self.config.get("backoff_factor", DEFAULT_BACKOFF_FACTOR)
        self.session_timeout = self.config.get("session_timeout", DEFAULT_SESSION_TIMEOUT)
        
        # Runtime state
        self.driver = None
        self.pending_queue = queue.Queue()
        self.is_running = False
        self.worker_thread = None
        self.last_session_time = 0
        self.session_valid = False
        
        # Create bridge inbox directory
        self.bridge_inbox = Path("runtime/bridge_inbox")
        self.bridge_inbox.mkdir(parents=True, exist_ok=True)
        self.pending_file = self.bridge_inbox / "pending_requests.json"
        
        # Initialize health check
        self.health_file = self.bridge_inbox / "bridge_ready.json"
        self._update_health(True)
        
        # Initialize logging
        self.logger.info(
            platform="chatgpt_bridge",
            status="initialized",
            message="ChatGPT bridge initialized",
            tags=["init", "bridge"]
        )
    
    def _load_health(self) -> Dict[str, Any]:
        """Load current health status.
        
        Returns:
            Dict containing health status
        """
        try:
            if not self.health_file.exists():
                return {"ready": False, "error": "Health file not found"}
            
            with open(self.health_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            return {"ready": False, "error": str(e)}
    
    def _update_health(self, ready: bool, error: Optional[str] = None):
        """Update bridge health status.
        
        Args:
            ready: Whether bridge is ready
            error: Optional error message
        """
        health = {
            "ready": ready,
            "last_check": time.time(),
            "error": error
        }
        
        with open(self.health_file, 'w') as f:
            json.dump(health, f, indent=2)
    
    def start(self):
        """Start the bridge worker thread."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        
        self._update_health(True)
        
        self.logger.info(
            platform="chatgpt_bridge",
            status="started",
            message="ChatGPT bridge worker started",
            tags=["start", "bridge"]
        )
    
    def stop(self):
        """Stop the bridge worker thread."""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5.0)
        if self.driver:
            self.driver.quit()
        
        self._update_health(False, "Bridge stopped")
        
        self.logger.info(
            platform="chatgpt_bridge",
            status="stopped",
            message="ChatGPT bridge worker stopped",
            tags=["stop", "bridge"]
        )
    
    async def request_chatgpt_response(self, agent_id: str, prompt: str) -> None:
        """Request a response from ChatGPT for an agent.
        
        Args:
            agent_id: ID of the requesting agent
            prompt: Text prompt to send to ChatGPT
        """
        if not agent_id.startswith("Agent-"):
            raise ValueError("Invalid agent ID format")
            
        try:
            request = {
                "agent_id": agent_id,
                "prompt": prompt,
                "timestamp": time.time()
            }
            
            # Add to queue
            self.pending_queue.put(request)
            
            # Save pending requests
            pending = list(self.pending_queue.queue)
            self._save_pending_requests(pending)
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="queued",
                message=f"Queued request for agent {agent_id}",
                tags=["request", "queue"]
            )
            
        except Exception as e:
            error_msg = f"Failed to queue request: {str(e)}"
            self._update_health(False, error_msg)
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=error_msg,
                tags=["request", "error"]
            )
            raise

    async def process_pending(self) -> None:
        """
        Process all pending ChatGPT requests in the internal queue.

        This method is intended for test environments or controlled execution flows
        where background threads are not started. It ensures deterministic
        processing of queued messages, mimicking bridge thread behavior.

        Logs all handled requests and preserves compatibility with the
        CellPhone message pipeline.

        Usage:
            await bridge.process_pending()
        """
        while not self.pending_queue.empty():
            request = self.pending_queue.get()
            self._process_request(request)
            
        # Update pending requests file
        pending = list(self.pending_queue.queue)
        self._save_pending_requests(pending)
        
        self.logger.info(
            platform="chatgpt_bridge",
            status="processed",
            message="Processed all pending requests",
            tags=["process", "queue"]
        )
    
    def _process_request(self, request):
        """Process a single request from the queue."""
        try:
            # Get agent ID and prompt from request
            agent_id = request.get("agent_id", "agent-unknown")
            prompt = request.get("prompt", "")
            
            if not prompt:
                return
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="processing",
                message=f"Processing request from {agent_id}",
                tags=["process", "request"]
            )
            
            # Send prompt to ChatGPT
            response = self._send_prompt(prompt)
            
            # Send response back to agent
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                asyncio.create_task(
                    self.cell_phone.send_message(
                        to_agent=agent_id,
                        content=response,
                        mode="SYSTEM",
                        from_agent="chatgpt_bridge",
                        metadata={"tags": ["bridge_response"]}
                    )
                )
            else:
                # If we're not in an async context, run the coroutine
                loop.run_until_complete(
                    self.cell_phone.send_message(
                        to_agent=agent_id,
                        content=response,
                        mode="SYSTEM",
                        from_agent="chatgpt_bridge",
                        metadata={"tags": ["bridge_response"]}
                    )
                )
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="success",
                message=f"Successfully processed request from {agent_id}",
                tags=["process", "success"]
            )
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, create a task
                asyncio.create_task(
                    self.cell_phone.send_message(
                        to_agent=agent_id,
                        content=f"Error: {error_msg}",
                        mode="SYSTEM",
                        from_agent="chatgpt_bridge",
                        metadata={"tags": ["bridge_error"]}
                    )
                )
            else:
                # If we're not in an async context, run the coroutine
                loop.run_until_complete(
                    self.cell_phone.send_message(
                        to_agent=agent_id,
                        content=f"Error: {error_msg}",
                        mode="SYSTEM",
                        from_agent="chatgpt_bridge",
                        metadata={"tags": ["bridge_error"]}
                    )
                )
            
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=error_msg,
                tags=["process", "error"]
            )
            # Re-queue failed request
            self.pending_queue.put(request)
    
    def _worker_loop(self):
        """Main worker loop for processing requests."""
        while self.is_running:
            try:
                # Check for pending requests
                if not self.pending_queue.empty():
                    request = self.pending_queue.get()
                    self._process_request(request)
                    self.pending_queue.task_done()
                
                # Save current queue state
                pending = list(self.pending_queue.queue)
                if pending:
                    self._save_pending_requests(pending)
                
                # Update health check
                self._update_health(True)
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = f"Error in worker loop: {str(e)}"
                self._update_health(False, error_msg)
                self.logger.error(
                    platform="chatgpt_bridge",
                    status="error",
                    message=error_msg,
                    tags=["worker", "error"]
                )
                time.sleep(1)  # Back off on error

    def _ensure_valid_session(self):
        """Ensure we have a valid ChatGPT session."""
        current_time = time.time()
        
        # Check if session needs refresh
        if (not self.session_valid or 
            current_time - self.last_session_time > self.session_timeout):
            
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
            
            try:
                self._launch_browser()
                self._handle_login()
                self.session_valid = True
                self.last_session_time = current_time
                self._update_health(True)
            except Exception as e:
                self.session_valid = False
                self._update_health(False, str(e))
                raise
    
    def _handle_login(self):
        """Handle ChatGPT login flow."""
        try:
            # Wait for login button or chat interface
            wait = WebDriverWait(self.driver, self.page_load_wait)
            
            # Check if we need to log in
            try:
                login_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Log in')]"))
                )
                if login_button.is_displayed():
                    self.logger.info(
                        platform="chatgpt_bridge",
                        status="login_required",
                        message="Login required - please log in manually",
                        tags=["login", "required"]
                    )
                    # Wait for manual login
                    wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[tabindex='0']"))
                    )
            except TimeoutException:
                # Already logged in
                pass
            
            # Verify we can access the chat interface
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[tabindex='0']"))
            )
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="success",
                message="Successfully verified ChatGPT session",
                tags=["login", "success"]
            )
            
        except Exception as e:
            self._update_health(False, f"Login failed: {str(e)}")
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=f"Login verification failed: {str(e)}",
                tags=["login", "error"]
            )
            raise
    
    def _launch_browser(self):
        """Launch undetected Chrome with user profile."""
        try:
            options = uc.ChromeOptions()
            options.add_argument(f"--user-data-dir={self.user_data_dir}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            self.driver = uc.Chrome(options=options)
            self.driver.get("https://chat.openai.com/")
            
            # Wait for page load
            WebDriverWait(self.driver, self.page_load_wait).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="success",
                message="ChatGPT browser launched successfully",
                tags=["browser", "launch"]
            )
        except Exception as e:
            self._update_health(False, f"Browser launch failed: {str(e)}")
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=f"Failed to launch browser: {str(e)}",
                tags=["browser", "error"]
            )
            raise
    
    def _send_prompt(self, prompt_text: str) -> str:
        """Send prompt to ChatGPT with retry logic."""
        attempt = 0
        wait_time = self.response_wait
        
        while attempt < self.max_retries:
            try:
                # Ensure valid session
                self._ensure_valid_session()
                
                # Find and interact with textarea
                wait = WebDriverWait(self.driver, self.page_load_wait)
                textarea = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[tabindex='0']"))
                )
                
                # Clear and send text
                textarea.clear()
                textarea.send_keys(prompt_text)
                textarea.send_keys(Keys.ENTER)
                
                self.logger.info(
                    platform="chatgpt_bridge",
                    status="sent",
                    message=f"Prompt sent (attempt {attempt+1}): {prompt_text[:50]}...",
                    tags=["prompt", "send"]
                )
                
                # Wait for response
                time.sleep(wait_time)
                
                # Get response
                messages = wait.until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.markdown"))
                )
                
                if not messages:
                    raise NoSuchElementException("No response elements found")
                    
                response = messages[-1].text.strip()
                if not response:
                    raise TimeoutException("Empty response text")
                    
                self.logger.info(
                    platform="chatgpt_bridge",
                    status="success",
                    message=f"Got response for prompt: {prompt_text[:50]}...",
                    tags=["prompt", "response"]
                )
                
                return response
                
            except (NoSuchElementException, TimeoutException, WebDriverException) as e:
                attempt += 1
                self.logger.warning(
                    platform="chatgpt_bridge",
                    status="retry",
                    message=f"Attempt {attempt}/{self.max_retries} failed: {str(e)}",
                    tags=["prompt", "retry"]
                )
                
                if attempt < self.max_retries:
                    time.sleep(wait_time)
                    wait_time *= self.backoff_factor
                else:
                    error_msg = f"Max retries reached for prompt: {prompt_text[:50]}..."
                    self._update_health(False, error_msg)
                    self.logger.error(
                        platform="chatgpt_bridge",
                        status="error",
                        message=error_msg,
                        tags=["prompt", "error"]
                    )
                    raise
    
    def _focus_cursor_window(self):
        """Focus the Cursor window."""
        try:
            windows = gw.getWindowsWithTitle(self.cursor_window_title)
            if not windows:
                raise RuntimeError(f"No window found with title containing '{self.cursor_window_title}'")
            
            # Try to activate window
            window = windows[0]
            if not window.isActive:
                window.activate()
                time.sleep(0.2)
                
                # Verify activation
                if not window.isActive:
                    raise RuntimeError("Failed to activate Cursor window")
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="success",
                message="Successfully focused Cursor window",
                tags=["window", "focus"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=f"Failed to focus Cursor window: {str(e)}",
                tags=["window", "error"]
            )
            raise

    def _paste_to_cursor(self, text: str):
        """Paste text into Cursor window."""
        try:
            if 'pyautogui' not in globals():
                self.logger.error("pyautogui not available; cannot paste to Cursor")
                return

            # Focus window first
            self._focus_cursor_window()

            # Type text with small delay between characters
            pyautogui.write(text, interval=0.01)
            time.sleep(0.1)  # Small pause before enter
            pyautogui.press("enter")
            time.sleep(self.paste_delay)
            
            self.logger.info(
                platform="chatgpt_bridge",
                status="success",
                message="Pasted response into Cursor",
                tags=["paste", "success"]
            )
        except Exception as e:
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=f"Failed to paste to Cursor: {str(e)}",
                tags=["paste", "error"]
            )
            raise
    
    def _load_pending_requests(self) -> List[Dict[str, Any]]:
        """Load pending requests from JSON file."""
        try:
            if not self.pending_file.exists():
                return []
                
            with open(self.pending_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("pending_requests.json is not a list")
                return data
        except Exception as e:
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=f"Failed to load pending requests: {str(e)}",
                tags=["load", "error"]
            )
            # Reset file to empty list
            self._save_pending_requests([])
            return []
    
    def _save_pending_requests(self, requests: List[Dict[str, Any]]):
        """Save pending requests to file."""
        try:
            with open(self.pending_file, "w") as f:
                json.dump(requests, f, indent=2)
        except Exception as e:
            self.logger.error(
                platform="chatgpt_bridge",
                status="error",
                message=f"Failed to save pending requests: {str(e)}",
                tags=["save", "error"]
            )

    def _worker_loop(self):
        """Main worker loop for processing requests."""
        while self.is_running:
            try:
                # Check for pending requests
                if not self.pending_queue.empty():
                    request = self.pending_queue.get()
                    self._process_request(request)
                    self.pending_queue.task_done()
                
                # Save current queue state
                pending = list(self.pending_queue.queue)
                if pending:
                    self._save_pending_requests(pending)
                
                # Update health check
                self._update_health(True)
                
                # Small sleep to prevent CPU spinning
                time.sleep(0.1)
                
            except Exception as e:
                error_msg = f"Error in worker loop: {str(e)}"
                self._update_health(False, error_msg)
                self.logger.error(
                    platform="chatgpt_bridge",
                    status="error",
                    message=error_msg,
                    tags=["worker", "error"]
                )
                time.sleep(1)  # Back off on error 