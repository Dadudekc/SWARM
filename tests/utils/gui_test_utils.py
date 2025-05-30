"""Utilities for GUI testing configuration and environment detection."""

import os
import sys
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def is_headless_environment() -> bool:
    """
    Detect if we're running in a headless environment.
    Returns True if running in CI, container, or no display is available.
    """
    # Check for common CI environment variables
    if any(var in os.environ for var in ['CI', 'TRAVIS', 'CIRCLECI', 'JENKINS_URL']):
        return True
        
    # Check for display on Unix-like systems
    if sys.platform != 'win32':
        return not os.environ.get('DISPLAY')
        
    # Windows-specific checks
    if sys.platform == 'win32':
        try:
            import win32gui
            return not win32gui.GetDesktopWindow()
        except ImportError:
            logger.warning("win32gui not available, assuming headless environment")
            return True
            
    return False

def get_display_info() -> Optional[tuple]:
    """
    Get display information if available.
    Returns (width, height) tuple or None if not available.
    """
    try:
        import pyautogui
        return pyautogui.size()
    except Exception as e:
        logger.warning(f"Could not get display info: {e}")
        return None

def should_skip_gui_test() -> bool:
    """
    Determine if GUI tests should be skipped based on environment.
    """
    if is_headless_environment():
        logger.info("Running in headless environment - GUI tests will be skipped")
        return True
    return False 