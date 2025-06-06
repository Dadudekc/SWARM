"""
ChatGPT Bridge Loop
------------------
Handles autonomous communication between agents and ChatGPT via Cursor.
"""

import json
import time
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pyautogui
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bridge.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChatGPTBridgeLoop:
    """Handles the autonomous ChatGPT ↔ Agent ↔ Cursor relay loop."""
    
    def __init__(self, config_path: str = "config/bridge_config.json"):
        """Initialize the bridge loop with configuration."""
        self.config = self._load_config(config_path)
        self.bridge_outbox = Path("bridge_outbox")
        self.agent_mailbox = Path("agent_tools/mailbox")
        self.coords_file = Path("cursor_agent_coords.json")
        self.coords = self._load_coords()
        self.driver = None
        self.wait_time = 5  # Default wait time for elements
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load bridge configuration."""
        try:
            with open(config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return {
                "chatgpt_url": "https://chat.openai.com",
                "poll_interval": 30,
                "max_retries": 3
            }
            
    def _load_coords(self) -> Dict[str, Dict[str, int]]:
        """Load cursor coordinates for each agent."""
        try:
            with open(self.coords_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Coordinates file {self.coords_file} not found")
            return {}
            
    def _init_browser(self):
        """Initialize undetected Chrome browser."""
        options = uc.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = uc.Chrome(options=options)
        self.driver.get(self.config["chatgpt_url"])
        
    def _wait_for_element(self, by: By, value: str, timeout: int = None) -> Any:
        """Wait for an element to be present and return it."""
        timeout = timeout or self.wait_time
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        
    def _submit_prompt(self, prompt: str) -> bool:
        """Submit a prompt to ChatGPT and wait for response."""
        try:
            # Find and click the input field
            input_field = self._wait_for_element(By.CSS_SELECTOR, "textarea[data-id='root']")
            input_field.clear()
            input_field.send_keys(prompt)
            
            # Find and click the submit button
            submit_button = self._wait_for_element(By.CSS_SELECTOR, "button[data-testid='send-button']")
            submit_button.click()
            
            # Wait for response
            response = self._wait_for_element(By.CSS_SELECTOR, "div[data-message-author-role='assistant']")
            return response.text
            
        except Exception as e:
            logger.error(f"Error submitting prompt: {e}")
            return None
            
    def _write_to_inbox(self, agent_id: str, response: str):
        """Write ChatGPT response to agent's inbox."""
        inbox_path = self.agent_mailbox / f"agent-{agent_id}" / "workspace" / "inbox.json"
        try:
            # Create directory if it doesn't exist
            inbox_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read existing inbox or create new
            if inbox_path.exists():
                with open(inbox_path) as f:
                    inbox = json.load(f)
            else:
                inbox = {"messages": []}
                
            # Add new message
            inbox["messages"].append({
                "timestamp": datetime.now().isoformat(),
                "content": response,
                "source": "chatgpt_bridge"
            })
            
            # Write back to file
            with open(inbox_path, 'w') as f:
                json.dump(inbox, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error writing to inbox: {e}")
            
    def _inject_to_cursor(self, agent_id: str, response: str):
        """Inject response into Cursor using PyAutoGUI."""
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for agent {agent_id}")
                return
                
            coords = self.coords[agent_id]
            pyautogui.click(coords["x"], coords["y"])
            pyautogui.write(response)
            pyautogui.press('enter')
            
        except Exception as e:
            logger.error(f"Error injecting to Cursor: {e}")
            
    def _process_outbox(self):
        """Process all pending prompts in the bridge outbox."""
        for prompt_file in self.bridge_outbox.glob("agent-*.json"):
            try:
                with open(prompt_file) as f:
                    prompt_data = json.load(f)
                    
                agent_id = prompt_file.stem.split('-')[1]
                prompt = prompt_data.get("prompt")
                
                if not prompt:
                    logger.warning(f"No prompt found in {prompt_file}")
                    continue
                    
                # Submit to ChatGPT
                response = self._submit_prompt(prompt)
                if not response:
                    logger.error(f"Failed to get response for {agent_id}")
                    continue
                    
                # Write to inbox
                self._write_to_inbox(agent_id, response)
                
                # Inject to Cursor
                self._inject_to_cursor(agent_id, response)
                
                # Archive processed prompt
                archive_path = prompt_file.parent / "archive" / prompt_file.name
                archive_path.parent.mkdir(exist_ok=True)
                prompt_file.rename(archive_path)
                
            except Exception as e:
                logger.error(f"Error processing {prompt_file}: {e}")
                
    def run(self):
        """Run the bridge loop continuously."""
        logger.info("Starting ChatGPT Bridge Loop")
        
        try:
            self._init_browser()
            
            while True:
                self._process_outbox()
                time.sleep(self.config["poll_interval"])
                
        except KeyboardInterrupt:
            logger.info("Bridge loop stopped by user")
        except Exception as e:
            logger.error(f"Bridge loop error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                
if __name__ == "__main__":
    bridge = ChatGPTBridgeLoop()
    bridge.run() 