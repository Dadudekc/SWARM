"""
Prompt Engine

Handles direct interaction with ChatGPT interface.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
    StaleElementReferenceException
)

from .browser_control import BrowserControl
from ..config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class PromptEngine:
    """Handles direct interaction with ChatGPT interface."""
    
    def __init__(self, config_path: str):
        """Initialize prompt engine.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_manager = ConfigManager()
        self.config = self.config_manager.get_bridge_config()
        
        self.browser = BrowserControl(
            user_data_dir=self.config.get('user_data_dir'),
            window_title=self.config.get('cursor_window_title'),
            page_load_wait=self.config.get('page_load_wait', 30),
            response_wait=self.config.get('response_wait', 15),
            paste_delay=self.config.get('paste_delay', 0.5)
        )
        
        self.templates_dir = Path("templates/prompts")
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        
    def start(self):
        """Start the prompt engine."""
        self.browser.start()
        logger.info("Prompt engine started")
        
    def stop(self):
        """Stop the prompt engine."""
        self.browser.stop()
        logger.info("Prompt engine stopped")
        
    def send_prompt(
        self,
        prompt: str,
        use_typing: bool = True,
        wait_for_completion: bool = True
    ) -> Optional[str]:
        """Send prompt to ChatGPT.
        
        Args:
            prompt: Prompt to send
            use_typing: Whether to simulate typing
            wait_for_completion: Whether to wait for response
            
        Returns:
            Response text or None
        """
        try:
            # Wait for input
            self.browser.wait_for_stable_element(
                "textarea",
                by=By.TAG_NAME,
                stability_time=2.0
            )
            
            # Send prompt
            if use_typing:
                self._type_prompt(prompt)
            else:
                self._inject_prompt(prompt)
                
            # Submit
            self.browser.click("button[type='submit']")
            
            # Wait for response if requested
            if wait_for_completion:
                return self.wait_for_completion()
                
            return None
            
        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            return None
            
    def _type_prompt(self, prompt: str):
        """Simulate typing prompt.
        
        Args:
            prompt: Prompt to type
        """
        self.browser.send_keys("textarea", prompt)
        
    def _inject_prompt(self, prompt: str):
        """Inject prompt via JavaScript.
        
        Args:
            prompt: Prompt to inject
        """
        script = f"""
        var textarea = document.querySelector('textarea');
        textarea.value = `{prompt}`;
        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
        """
        self.browser.driver.execute_script(script)
        
    def wait_for_completion(
        self,
        timeout: int = 60,
        stability_period: int = 5,
        check_interval: float = 1.0
    ) -> Optional[str]:
        """Wait for response completion.
        
        Args:
            timeout: Maximum wait time
            stability_period: Time response must be stable
            check_interval: Time between checks
            
        Returns:
            Response text or None
        """
        start_time = time.time()
        last_response = None
        stable_start = None
        
        while time.time() - start_time < timeout:
            try:
                # Get latest response
                response_element = self.browser.wait_for_element(
                    "div[data-message-author-role='assistant']:last-child",
                    timeout=1
                )
                current_response = response_element.text.strip()
                
                # Check for completion
                if self._is_response_complete(response_element):
                    if current_response == last_response:
                        if stable_start is None:
                            stable_start = time.time()
                        elif time.time() - stable_start >= stability_period:
                            return current_response
                    else:
                        stable_start = None
                        
                last_response = current_response
                time.sleep(check_interval)
                
            except (TimeoutException, StaleElementReferenceException):
                continue
                
        return last_response
        
    def _is_response_complete(self, element) -> bool:
        """Check if response is complete.
        
        Args:
            element: Response element
            
        Returns:
            Whether response is complete
        """
        try:
            # Check for typing indicator
            typing_indicators = element.find_elements(
                By.CSS_SELECTOR,
                "div[data-testid='typing-indicator']"
            )
            if typing_indicators:
                return False
                
            # Check for incomplete markdown
            text = element.text
            if text.count("```") % 2 != 0:
                return False
                
            return True
            
        except Exception:
            return False
            
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history.
        
        Returns:
            List of conversation messages
        """
        try:
            messages = []
            elements = self.browser.driver.find_elements(
                By.CSS_SELECTOR,
                "div[data-message-author-role]"
            )
            
            for element in elements:
                role = element.get_attribute("data-message-author-role")
                text = element.text.strip()
                if text:
                    messages.append({
                        "role": role,
                        "content": text
                    })
                    
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
            
    def clear_conversation(self):
        """Clear current conversation."""
        try:
            # Click new chat button
            self.browser.click("a[href='/']")
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.browser.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 