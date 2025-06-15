"""Prompt execution helpers for the ChatGPT bridge."""

import time
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

import logging

logger = logging.getLogger('chatgpt_bridge')


class PromptExecutionService:
    """Handles prompt execution and response retrieval."""

    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver

    def get_prompt(self, prompt_name: str) -> str:
        """Get prompt text from prompts directory."""
        prompt_file = Path(f"prompts/{prompt_name}.txt")
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        return prompt_file.read_text().strip()

    def send_prompt_and_wait(self, prompt_text: str) -> str:
        """Send prompt to ChatGPT and wait for response."""
        try:
            textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[data-id='root']"))
            )
            textarea.clear()
            textarea.send_keys(prompt_text)
            textarea.send_keys(Keys.ENTER)
            time.sleep(2)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.result-streaming"))
            )
            response_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.markdown")
            if not response_elements:
                raise NoSuchElementException("No response found")
            return response_elements[-1].text.strip()
        except (TimeoutException, NoSuchElementException) as exc:
            logger.error("Failed to get ChatGPT response: %s", exc)
            raise

__all__ = ["PromptExecutionService"]
