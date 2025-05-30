"""
Timing configuration for UI automation.

This module defines standard delays for UI automation actions to ensure
consistent timing across the application. All delays are in seconds.
"""

import time

# Window focus and activation delays
WINDOW_ACTIVATION_DELAY = 1.0  # Time to wait after clicking to activate window
FOCUS_ESTABLISH_DELAY = 0.5    # Time to wait after focusing input box

# Text manipulation delays
TEXT_CLEAR_DELAY = 0.2        # Time to wait after Ctrl+A
TEXT_DELETE_DELAY = 0.5       # Time to wait after Delete
TYPING_INTERVAL = 0.1         # Time between keystrokes
TYPING_COMPLETE_DELAY = 0.5   # Time to wait after typing completes

# Message sending delays
MESSAGE_SEND_DELAY = 1.0      # Time to wait after pressing Enter
COPY_BUTTON_DELAY = 0.5       # Time to wait after clicking copy button

# Response capture delays
RESPONSE_CAPTURE_DELAY = 0.5  # Time to wait before capturing response

# Debug delays
DEBUG_SCREENSHOT_DELAY = 0.2  # Time to wait before taking debug screenshots

class Timing:
    """Minimal Timing stub for UI/automation flow compatibility."""
    
    def __init__(self):
        """Initialize timing constants."""
        # UI interaction delays
        self.focus_delay = 0.3  # Time to wait after focusing an element
        self.click_delay = 0.2  # Time to wait after clicking
        self.typing_delay = 0.05  # Delay between keystrokes
        self.capture_delay = 0.4  # Time to wait before capturing response
        self.screenshot_delay = 0.5  # Time to wait before taking screenshot
        
        # Movement delays
        self.move_delay = 0.5  # Time to wait after cursor movement
        self.scroll_delay = 0.3  # Time to wait after scrolling
        
        # System delays
        self.load_delay = 1.0  # Time to wait for page/component load
        self.refresh_delay = 2.0  # Time to wait for refresh/update
        
    def wait_focus(self) -> None:
        """Wait for focus delay."""
        time.sleep(self.focus_delay)
        
    def wait_click(self) -> None:
        """Wait for click delay."""
        time.sleep(self.click_delay)
        
    def wait_typing(self) -> None:
        """Wait for typing delay."""
        time.sleep(self.typing_delay)
        
    def wait_capture(self) -> None:
        """Wait for capture delay."""
        time.sleep(self.capture_delay)
        
    def wait_screenshot(self) -> None:
        """Wait for screenshot delay."""
        time.sleep(self.screenshot_delay)
        
    def wait_move(self) -> None:
        """Wait for movement delay."""
        time.sleep(self.move_delay)
        
    def wait_scroll(self) -> None:
        """Wait for scroll delay."""
        time.sleep(self.scroll_delay)
        
    def wait_load(self) -> None:
        """Wait for load delay."""
        time.sleep(self.load_delay)
        
    def wait_refresh(self) -> None:
        """Wait for refresh delay."""
        time.sleep(self.refresh_delay) 