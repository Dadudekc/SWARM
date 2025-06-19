"""Selenium driver management for the ChatGPT bridge."""

import os
from selenium import webdriver


class DriverManager:
    """Manages the Chrome WebDriver instance."""

    def __init__(self):
        self.driver = None
        self.client = None

    def setup(self):
        """Initialize and return a Chrome browser instance."""
        if os.getenv("CHATGPT_STEALTH") == "1":
            from tools.core.bridge.openai_client import OpenAIClient
            self.client = OpenAIClient(profile_dir="chrome_profile")
            self.client.login_openai()
            self.driver = self.client.driver
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            self.driver = webdriver.Chrome(options=options)
        return self.driver

    def quit(self):
        """Clean up the driver instance."""
        if self.client:
            self.client.shutdown()
            self.client = None
        elif self.driver:
            self.driver.quit()
        self.driver = None

__all__ = ["DriverManager"]
