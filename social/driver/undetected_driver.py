import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class UndetectedDriver:
    """Wrapper for undetected-chromedriver with anti-bot evasion capabilities."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        headless: bool = False,
        window_title: Optional[str] = None,
        window_coords: Optional[Dict[str, int]] = None
    ):
        """Initialize the undetected driver.
        
        Args:
            config: Configuration dictionary
            headless: Whether to run in headless mode
            window_title: Optional window title
            window_coords: Optional window coordinates
        """
        self.config = config
        self.headless = headless
        self.window_title = window_title
        self.window_coords = window_coords
        self.driver = None
        
    def create_driver(self) -> uc.Chrome:
        """Create and configure the undetected Chrome driver.
        
        Returns:
            Configured undetected Chrome driver instance
        """
        options = uc.ChromeOptions()
        
        # Add anti-detection options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--dns-prefetch-disable')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Add user agent if specified
        if 'user_agent' in self.config:
            options.add_argument(f'--user-agent={self.config["user_agent"]}')
            
        # Add proxy if specified
        if 'proxy' in self.config:
            options.add_argument(f'--proxy-server={self.config["proxy"]}')
            
        # Set window size and position if specified
        if self.window_coords:
            options.add_argument(f'--window-size={self.window_coords["width"]},{self.window_coords["height"]}')
            options.add_argument(f'--window-position={self.window_coords["x"]},{self.window_coords["y"]}')
            
        # Set headless mode if specified
        if self.headless:
            options.add_argument('--headless')
            
        try:
            logger.info("Launching undetected Chrome...")
            driver = uc.Chrome(options=options)
            
            # Set window title if specified
            if self.window_title:
                driver.execute_script(f'document.title = "{self.window_title}";')
                
            logger.info("Undetected Chrome launched successfully")
            return driver
            
        except Exception as e:
            logger.error(f"Failed to launch undetected Chrome: {str(e)}")
            raise
            
    def get_driver(self) -> uc.Chrome:
        """Get or create the driver instance.
        
        Returns:
            Undetected Chrome driver instance
        """
        if not self.driver:
            self.driver = self.create_driver()
        return self.driver
        
    def quit(self) -> None:
        """Quit the driver if it exists."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {str(e)}")
            finally:
                self.driver = None 
