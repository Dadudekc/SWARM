"""
Cursor Controller

Provides cursor control functionality for agent interaction.
"""

import logging
import time
import pyautogui
from typing import Optional, Tuple
from .utils.core_utils import transform_coordinates

logger = logging.getLogger('cursor_controller')

class CursorController:
    """Controls cursor movement and input for agent interaction."""
    
    def __init__(self):
        # Set up PyAutoGUI settings
        pyautogui.FAILSAFE = False  # Disable fail-safe for automated operation
        pyautogui.PAUSE = 0.1  # Add small delay between actions
        
    def move_to(self, x: int, y: int):
        """Move cursor to specified coordinates
        
        Args:
            x: X coordinate (0 to screen_width, or negative for right-edge offset)
            y: Y coordinate (0 to screen_height)
        """
        try:
            # Transform coordinates using shared utility
            x, y = transform_coordinates(x, y)
            
            # Move cursor
            pyautogui.moveTo(x, y)
            logger.debug(f"Cursor moved to: ({x}, {y})")
        except Exception as e:
            logger.error(f"Error moving cursor: {e}")
            raise
            
    def click(self):
        """Perform a mouse click at current position"""
        try:
            pyautogui.click()
            logger.debug("Performed mouse click")
        except Exception as e:
            logger.error(f"Error performing click: {e}")
            raise
            
    def type_text(self, text: str):
        """Type text at current position
        
        Args:
            text: Text to type, can include newlines
        """
        try:
            # Split text into lines and type each line
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if i > 0:  # For all lines after the first
                    pyautogui.press('enter')  # Press enter to move to next line
                    time.sleep(0.1)  # Small delay between lines
                pyautogui.write(line)
                logger.debug(f"Typed line {i+1}: {line[:30]}...")
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            raise
            
    def press_enter(self):
        """Press Enter key"""
        try:
            time.sleep(0.2)  # Small delay before pressing
            pyautogui.hotkey('enter')
            time.sleep(0.2)  # Small delay after pressing
            logger.debug("Pressed Enter key")
        except Exception as e:
            logger.error(f"Error pressing Enter: {e}")
            raise
            
    def press_ctrl_enter(self):
        """Press Ctrl+Enter combination"""
        try:
            pyautogui.hotkey('ctrl', 'enter')
            logger.debug("Pressed Ctrl+Enter")
        except Exception as e:
            logger.error(f"Error pressing Ctrl+Enter: {e}")
            raise
            
    def press_ctrl_n(self):
        """Press Ctrl+N combination"""
        try:
            pyautogui.hotkey('ctrl', 'n')
            logger.debug("Pressed Ctrl+N")
        except Exception as e:
            logger.error(f"Error pressing Ctrl+N: {e}")
            raise
            
    def press_ctrl_v(self):
        """Press Ctrl+V combination"""
        try:
            pyautogui.hotkey('ctrl', 'v')
            logger.debug("Pressed Ctrl+V")
        except Exception as e:
            logger.error(f"Error pressing Ctrl+V: {e}")
            raise
            
    def press_ctrl_a(self):
        """Press Ctrl+A combination"""
        try:
            pyautogui.hotkey('ctrl', 'a')
            logger.debug("Pressed Ctrl+A")
        except Exception as e:
            logger.error(f"Error pressing Ctrl+A: {e}")
            raise 