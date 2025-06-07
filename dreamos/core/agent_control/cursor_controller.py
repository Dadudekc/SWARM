"""
Cursor controller for UI automation.
"""

import time
from typing import Tuple, Optional
import pyautogui

from dreamos.core.shared.coordinate_manager import CoordinateManager
from .timing import Timing

class CursorController:
    """Controls cursor movement and interaction."""
    
    def __init__(self, coordinate_manager: Optional[CoordinateManager] = None):
        """Initialize cursor controller."""
        self.coordinate_manager = coordinate_manager or CoordinateManager()
        self.timing = Timing()
        
    def move_to(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Move cursor to coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration in seconds
            
        Returns:
            True if successful
        """
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            print(f"Failed to move cursor: {e}")
            return False
            
    def click(self, x: Optional[int] = None, y: Optional[int] = None) -> bool:
        """Click at coordinates or current position.
        
        Args:
            x: Optional X coordinate
            y: Optional Y coordinate
            
        Returns:
            True if successful
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y)
            else:
                pyautogui.click()
            return True
        except Exception as e:
            print(f"Failed to click: {e}")
            return False
            
    def type_text(self, text: str, interval: float = 0.1) -> bool:
        """Type text at current position.
        
        Args:
            text: Text to type
            interval: Delay between keystrokes
            
        Returns:
            True if successful
        """
        try:
            pyautogui.write(text, interval=interval)
            return True
        except Exception as e:
            print(f"Failed to type text: {e}")
            return False
            
    def press_enter(self) -> bool:
        """Press enter key.
        
        Returns:
            True if successful
        """
        try:
            pyautogui.press('enter')
            return True
        except Exception as e:
            print(f"Failed to press enter: {e}")
            return False
            
    def get_position(self) -> Tuple[int, int]:
        """Get current cursor position.
        
        Returns:
            (x, y) coordinates
        """
        return pyautogui.position()
        
    def wait(self, seconds: float) -> None:
        """Wait for specified duration.
        
        Args:
            seconds: Duration in seconds
        """
        time.sleep(seconds)
        
    def move_to_agent(self, agent_id: str) -> bool:
        """Move cursor to agent position.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful
        """
        coords = self.coordinate_manager.get_agent_coordinates(agent_id)
        if coords:
            return self.move_to(coords[0], coords[1])
        return False
        
    def click_input_box(self, agent_id: str) -> bool:
        """Click agent input box.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful
        """
        coords = self.coordinate_manager.get_input_box_coordinates(agent_id)
        if coords:
            return self.click(coords[0], coords[1])
        return False
        
    def click_copy_button(self, agent_id: str) -> bool:
        """Click agent copy button.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful
        """
        coords = self.coordinate_manager.get_copy_button_coordinates(agent_id)
        if coords:
            return self.click(coords[0], coords[1])
        return False 