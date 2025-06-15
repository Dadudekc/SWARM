"""Selenium driver management for the ChatGPT bridge."""

from selenium import webdriver


class DriverManager:
    """Manages the Chrome WebDriver instance."""

    def __init__(self):
        self.driver = None

    def setup(self):
        """Initialize and return a Chrome browser instance."""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        return self.driver

    def quit(self):
        """Clean up the driver instance."""
        if self.driver:
            self.driver.quit()
            self.driver = None

__all__ = ["DriverManager"]
