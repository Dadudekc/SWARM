"""
ChatGPT Bridge Loop Module

Handles the communication loop between the system and ChatGPT.
Manages browser automation and response processing.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
import os
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class ChatGPTBridgeLoop:
    """Handles the communication loop with ChatGPT."""
    
    def __init__(self, config_path: str):
        """Initialize the ChatGPT bridge loop.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.driver = None
        self.wait = None
        self.metrics_path = Path("data/metrics")
        self.metrics_path.mkdir(parents=True, exist_ok=True)
        self._init_metrics()
        self.is_running = False
        
    def _init_metrics(self):
        """Initialize metrics file."""
        metrics_file = self.metrics_path / "bridge_metrics.json"
        if not metrics_file.exists():
            metrics = {
                "processed_messages": 0,
                "failed_messages": 0,
                "total_response_time": 0,
                "last_processed": None
            }
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
    def _update_metrics(self, success: bool, response_time: float):
        """Update metrics.
        
        Args:
            success: Whether message was processed successfully
            response_time: Time taken to process message
        """
        metrics_file = self.metrics_path / "bridge_metrics.json"
        try:
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
                
            if success:
                metrics["processed_messages"] += 1
            else:
                metrics["failed_messages"] += 1
                
            metrics["total_response_time"] += response_time
            metrics["last_processed"] = time.time()
            
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error updating metrics: {e}")
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Dict containing configuration
        """
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    async def run(self):
        """Run the ChatGPT bridge loop."""
        try:
            # Initialize browser
            self._init_browser()
            
            # Navigate to ChatGPT
            self._navigate_to_chatgpt()
            
            # Wait for page load
            self._wait_for_page_load()
            
            self.is_running = True
            logger.info("ChatGPT bridge loop started")
            
            # Start message processing loop
            while self.is_running:
                try:
                    # Process any pending messages
                    await self._process_pending_messages()
                    
                    # Sleep briefly to avoid tight loop
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error in message processing loop: {e}")
                    # Update metrics for failure
                    self._update_metrics(success=False, response_time=0)
                    
        except Exception as e:
            logger.error(f"Error starting bridge loop: {e}")
            self.cleanup()
            
    async def _process_pending_messages(self):
        """Process any pending messages in the inbox."""
        try:
            # Get mailbox path from config
            mailbox_path = Path(self.config.get('paths', {}).get('mailbox', 'data/mailbox'))
            mailbox_path.mkdir(parents=True, exist_ok=True)
            
            # Look for message files in agent workspaces
            for agent_dir in mailbox_path.glob('agent-*'):
                workspace_dir = agent_dir / 'workspace'
                if not workspace_dir.exists():
                    continue
                    
                for msg_file in workspace_dir.glob('bridge_response.json'):
                    try:
                        # Read message
                        with open(msg_file) as f:
                            message = json.load(f)
                            
                        # Process message
                        start_time = time.time()
                        response = await self.send_message(message.get('content', ''))
                        
                        # Update metrics
                        response_time = time.time() - start_time
                        self._update_metrics(success=response is not None, response_time=response_time)
                        
                        # Move to archive
                        archive_path = Path(self.config.get('paths', {}).get('archive', 'data/archive'))
                        archive_path.mkdir(parents=True, exist_ok=True)
                        archive_file = archive_path / agent_dir.name / msg_file.name
                        archive_file.parent.mkdir(parents=True, exist_ok=True)
                        msg_file.rename(archive_file)
                        
                    except Exception as e:
                        logger.error(f"Error processing message {msg_file}: {e}")
                        # Move to failed
                        failed_path = Path(self.config.get('paths', {}).get('failed', 'data/failed'))
                        failed_path.mkdir(parents=True, exist_ok=True)
                        failed_file = failed_path / agent_dir.name / msg_file.name
                        failed_file.parent.mkdir(parents=True, exist_ok=True)
                        msg_file.rename(failed_file)
                        
        except Exception as e:
            logger.error(f"Error in message processing: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        self.is_running = False
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error cleaning up driver: {e}")
            finally:
                self.driver = None
                self.wait = None
                
    def _init_browser(self):
        """Initialize the browser."""
        try:
            # Set up Chrome options
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Initialize driver
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            
        except Exception as e:
            logger.error(f"Error initializing browser: {e}")
            raise
            
    def _navigate_to_chatgpt(self):
        """Navigate to ChatGPT."""
        try:
            self.driver.get(self.config.get('chatgpt_url', 'https://chat.openai.com'))
        except Exception as e:
            logger.error(f"Error navigating to ChatGPT: {e}")
            raise
            
    def _wait_for_page_load(self):
        """Wait for page to load."""
        try:
            # Wait for input box
            self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[data-id="root"]'))
            )
        except TimeoutException:
            logger.error("Timeout waiting for page load")
            raise
            
    async def send_message(self, message: str) -> Optional[str]:
        """Send a message to ChatGPT.
        
        Args:
            message: Message to send
            
        Returns:
            Optional[str]: Response from ChatGPT
        """
        start_time = time.time()
        try:
            # Check for test mode
            if os.getenv("DREAMOS_TEST_MODE") == "1":
                # Get agent ID from message if available
                agent_id = "1"  # Default to agent-1
                if isinstance(message, dict) and "agent_id" in message:
                    agent_id = message["agent_id"].split("-")[1]
                    
                # Get outbox path from config
                outbox_path = Path(self.config.get('paths', {}).get('outbox', 'data/outbox'))
                outbox_path.mkdir(parents=True, exist_ok=True)
                prompt_file = outbox_path / f"agent-{agent_id}.json"
                
                with open(prompt_file, "w") as f:
                    json.dump({
                        "role": "assistant",
                        "content": "Mock reply for testing",
                        "prompt": message if isinstance(message, str) else message.get("content", ""),
                        "timestamp": datetime.now().isoformat()
                    }, f, indent=2)
                    
                return "Mock reply for testing"
            
            # Find input box
            input_box = self.driver.find_element(By.CSS_SELECTOR, 'textarea[data-id="root"]')
            
            # Send message
            input_box.send_keys(message)
            input_box.submit()
            
            # Wait for response
            response = self._wait_for_response()
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_metrics(success=response is not None, response_time=response_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            # Update metrics for failure
            response_time = time.time() - start_time
            self._update_metrics(success=False, response_time=response_time)
            return None
            
    def _wait_for_response(self, timeout: int = 30) -> Optional[str]:
        """Wait for response from ChatGPT.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Optional[str]: Response text
        """
        try:
            # Wait for response element
            response_element = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '.markdown-content'))
            )
            
            # Get response text
            return response_element.text
            
        except TimeoutException:
            logger.error("Timeout waiting for response")
            return None
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            return None 