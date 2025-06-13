"""
Window Management Module

Handles window operations for agent recovery, including finding and activating
Cursor windows, checking window states, and managing window interactions.
"""

import logging
import time
from typing import Optional, List

import win32gui
import win32con
import win32process
import psutil

logger = logging.getLogger(__name__)

class WindowManager:
    """Manages window operations for agent recovery."""
    
    def __init__(self, cursor_window_class: str = "Chrome_WidgetWin_1"):
        """Initialize the window manager.
        
        Args:
            cursor_window_class: Window class name for Cursor windows
        """
        self.cursor_window_class = cursor_window_class
        self.last_activity: dict[str, float] = {}
        
    def find_cursor_window(self, agent_id: str) -> Optional[int]:
        """Find the Cursor window for a specific agent.
        
        Args:
            agent_id: ID of the agent to find window for
            
        Returns:
            Optional[int]: Window handle if found, None otherwise
        """
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                class_name = win32gui.GetClassName(hwnd)
                if class_name == self.cursor_window_class:
                    # Get window title
                    title = win32gui.GetWindowText(hwnd)
                    # Check if title contains agent ID
                    if agent_id in title:
                        windows.append(hwnd)
            return True
            
        windows = []
        win32gui.EnumWindows(callback, windows)
        return windows[0] if windows else None
        
    def check_window_idle(self, agent_id: str, idle_threshold: int) -> bool:
        """Check if a Cursor window is idle.
        
        Args:
            agent_id: ID of the agent to check
            idle_threshold: Time in seconds before window is considered idle
            
        Returns:
            bool: True if window is idle
        """
        try:
            hwnd = self.find_cursor_window(agent_id)
            if not hwnd:
                return False
                
            # Get process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid:
                return False
                
            # Get process
            process = psutil.Process(pid)
            
            # Check if process is responding
            if not process.is_running():
                return True
                
            # Check last activity time
            last_active = self.last_activity.get(agent_id, 0)
            if time.time() - last_active > idle_threshold:
                return True
                
            # Check if window is minimized
            if win32gui.IsIconic(hwnd):
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking Cursor idle state for agent {agent_id}: {e}")
            return False
            
    def activate_window(self, hwnd: int) -> bool:
        """Activate a window.
        
        Args:
            hwnd: Window handle to activate
            
        Returns:
            bool: True if activation successful
        """
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Error activating window {hwnd}: {e}")
            return False
            
    def update_activity(self, agent_id: str) -> None:
        """Update the last activity time for an agent.
        
        Args:
            agent_id: ID of the agent to update
        """
        self.last_activity[agent_id] = time.time() 