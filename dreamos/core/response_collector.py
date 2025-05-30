"""
Response Collector

Captures and saves Cursor agent responses programmatically for SWARM agents.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
import win32gui
import win32con
import win32clipboard
import keyboard
import re
import uiautomation as auto
import os
import pyautogui
import numpy as np
from PIL import Image, ImageChops
import cv2

logger = logging.getLogger('response_collector')

class CopyButtonDetector:
    """Detects and interacts with the copy button in Cursor."""
    
    def __init__(self, template_path: str = "templates/copy_button.png"):
        """Initialize the copy button detector.
        
        Args:
            template_path: Path to the template image of the copy button
        """
        self.template_path = template_path
        self.template = None
        self.load_template()
        
    def load_template(self) -> None:
        """Load the template image for copy button detection."""
        try:
            if os.path.exists(self.template_path):
                self.template = cv2.imread(self.template_path, cv2.IMREAD_COLOR)
                logger.info(f"Loaded copy button template from {self.template_path}")
            else:
                logger.warning(f"Template not found at {self.template_path}")
        except Exception as e:
            logger.error(f"Error loading template: {e}")
    
    def detect_copy_button(self, region: Tuple[int, int, int, int]) -> Optional[Tuple[int, int]]:
        """Detect copy button in the given region.
        
        Args:
            region: (left, top, right, bottom) coordinates to search in
            
        Returns:
            (x, y) coordinates of button center if found, None otherwise
        """
        try:
            if self.template is None:
                return None
                
            # Capture region screenshot
            screenshot = pyautogui.screenshot(region=region)
            screenshot_np = np.array(screenshot)
            screenshot_np = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)
            
            # Template matching
            result = cv2.matchTemplate(screenshot_np, self.template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            # If match confidence is high enough
            if max_val >= 0.8:  # Adjust threshold as needed
                # Get center of matched region
                h, w = self.template.shape[:2]
                center_x = max_loc[0] + w//2 + region[0]
                center_y = max_loc[1] + h//2 + region[1]
                logger.debug(f"Found copy button at ({center_x}, {center_y}) with confidence {max_val:.2f}")
                return (center_x, center_y)
                
            return None
            
        except Exception as e:
            logger.error(f"Error detecting copy button: {e}")
            return None
    
    def click_copy_button(self, region: Tuple[int, int, int, int]) -> bool:
        """Detect and click the copy button in the given region.
        
        Args:
            region: (left, top, right, bottom) coordinates to search in
            
        Returns:
            True if button was found and clicked, False otherwise
        """
        try:
            button_pos = self.detect_copy_button(region)
            if button_pos:
                x, y = button_pos
                pyautogui.click(x, y)
                logger.info(f"Clicked copy button at ({x}, {y})")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error clicking copy button: {e}")
            return False

class AgentRegion:
    """Defines a region for monitoring agent responses."""
    
    def __init__(self, name: str, region: Tuple[int, int, int, int], 
                 check_interval: float = 0.5, 
                 stability_threshold: float = 0.95,
                 agent_id: Optional[str] = None,
                 copy_button_region: Optional[Tuple[int, int, int, int]] = None):
        """Initialize an agent region.
        
        Args:
            name: Name of the region
            region: (left, top, right, bottom) coordinates of the region
            check_interval: How often to check for changes (seconds)
            stability_threshold: How similar consecutive screenshots must be to consider stable
            agent_id: Optional SWARM agent ID
            copy_button_region: Optional region where copy button appears
        """
        self.name = name
        self.region = region
        self.check_interval = check_interval
        self.stability_threshold = stability_threshold
        self.agent_id = agent_id
        self.copy_button_region = copy_button_region
        self.last_screenshot = None
        self.last_change_time = None
        self.copy_detector = CopyButtonDetector()
        
    def capture(self) -> Image.Image:
        """Capture the region screenshot."""
        return pyautogui.screenshot(region=self.region)
        
    def is_stable(self) -> bool:
        """Check if the region content has stabilized."""
        current = self.capture()
        
        if self.last_screenshot is None:
            self.last_screenshot = current
            self.last_change_time = time.time()
            return False
            
        # Compare current and last screenshot
        diff = ImageChops.difference(current, self.last_screenshot)
        similarity = 1.0 - (np.sum(diff) / (255.0 * diff.size[0] * diff.size[1]))
        
        if similarity < self.stability_threshold:
            # Content changed
            self.last_screenshot = current
            self.last_change_time = time.time()
            return False
            
        # Content stable for check_interval
        if time.time() - self.last_change_time >= self.check_interval:
            return True
            
        return False
        
    def try_copy_response(self) -> bool:
        """Attempt to copy the response using the copy button."""
        if self.copy_button_region:
            return self.copy_detector.click_copy_button(self.copy_button_region)
        return False

class ResponseCollector:
    """Collects and saves Cursor agent responses for SWARM."""
    
    def __init__(self, save_dir: str = "agent_responses", regions_file: str = "agent_regions.json"):
        """Initialize the response collector.
        
        Args:
            save_dir: Directory to save responses
            regions_file: Path to JSON file containing agent regions
        """
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(exist_ok=True)
        self.last_response = None
        self.response_count = 0
        self.cursor_windows = []  # List of all Cursor windows
        self.active_window = None  # Currently active Cursor window
        self.agent_regions = {}  # Dict of agent name to AgentRegion
        
        # Load agent regions from file
        self._load_agent_regions(regions_file)
        logger.info(f"Response collector initialized with save dir: {save_dir}")
    
    def _load_agent_regions(self, regions_file: str) -> None:
        """Load agent regions from JSON file."""
        try:
            with open(regions_file, 'r') as f:
                regions = json.load(f)
                
            for name, coords in regions.items():
                region = (
                    coords['left'],
                    coords['top'],
                    coords['right'],
                    coords['bottom']
                )
                # Extract agent ID from region name if present
                agent_id = None
                if '_' in name:
                    parts = name.split('_')
                    if len(parts) >= 2 and parts[0] == 'agent':
                        agent_id = parts[1]
                
                # Get copy button region if specified
                copy_button_region = None
                if 'copy_button' in coords:
                    copy_button_region = (
                        coords['copy_button']['left'],
                        coords['copy_button']['top'],
                        coords['copy_button']['right'],
                        coords['copy_button']['bottom']
                    )
                
                self.agent_regions[name] = AgentRegion(
                    name=name,
                    region=region,
                    agent_id=agent_id,
                    copy_button_region=copy_button_region
                )
                logger.info(f"Loaded region for {name}: {region}")
                if copy_button_region:
                    logger.info(f"Loaded copy button region: {copy_button_region}")
                
        except Exception as e:
            logger.error(f"Error loading agent regions: {e}")
    
    def _find_cursor_windows(self) -> bool:
        """Find all Cursor windows using UI Automation."""
        try:
            # Find all windows with "Cursor" in the title
            windows = auto.GetRootControl().GetChildren()
            for window in windows:
                if window.ControlType == auto.ControlType.WindowControl:
                    title = window.Name
                    if "Cursor" in title:
                        # Get the window handle
                        hwnd = window.NativeWindowHandle
                        if hwnd:
                            self.cursor_windows.append((hwnd, title))
                            logger.debug(f"Found Cursor window: {title} (Handle: {hwnd})")
            
            return len(self.cursor_windows) > 0
        except Exception as e:
            logger.error(f"Error finding Cursor windows: {e}")
            return False
    
    def _get_cursor_text(self) -> Optional[str]:
        """Get text from active Cursor window using UI Automation."""
        try:
            # Get active window
            active_window = auto.GetForegroundControl()
            if not active_window:
                logger.error("No active window found")
                return None
            
            # Check if active window is a Cursor window
            if "Cursor" not in active_window.Name:
                logger.debug(f"Active window is not Cursor: {active_window.Name}")
                return None
            
            # Find the response area - typically a rich text or edit control
            response_area = active_window.GetFirstChildControl(lambda c: (
                c.ControlType in [auto.ControlType.EditControl, 
                                auto.ControlType.DocumentControl,
                                auto.ControlType.TextControl] and
                c.IsEnabled and
                c.IsVisible
            ))
            
            if response_area:
                text = response_area.Name
                if text:
                    logger.debug(f"Got text from response area: {text[:100]}...")
                    return text
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Cursor text: {e}")
            return None
    
    def start_collecting(self, timeout: int = 300, agent_id: Optional[str] = None) -> bool:
        """Start collecting responses from Cursor.
        
        Args:
            timeout: Maximum time to wait for response in seconds
            agent_id: Optional SWARM agent ID to monitor
            
        Returns:
            True if response was collected, False if timeout
            
        Raises:
            ValueError: If timeout is negative
            OSError: If save directory is invalid or not writable
        """
        if timeout < 0:
            raise ValueError("Timeout must be non-negative")
            
        # Verify save directory is valid and writable
        if not os.path.exists(self.save_dir):
            raise OSError(f"Save directory does not exist: {self.save_dir}")
        if not os.access(self.save_dir, os.W_OK):
            raise OSError(f"Save directory is not writable: {self.save_dir}")
            
        try:
            # Find all Cursor windows
            if not self._find_cursor_windows():
                logger.error("Could not find any Cursor windows")
                return False
            
            logger.info(f"Found {len(self.cursor_windows)} Cursor windows")
            for hwnd, title in self.cursor_windows:
                logger.info(f"- {title} (Handle: {hwnd})")
            
            # Wait for response to start
            start_time = time.time()
            last_text = self._get_cursor_text()
            logger.debug(f"Initial text: {last_text[:100] if last_text else 'None'}")
            
            # Ensure we wait at least the full timeout period
            while True:
                current_time = time.time()
                elapsed = current_time - start_time
                
                if elapsed >= timeout:
                    logger.warning("Response collection timed out")
                    return False
                    
                # Check if new content in Cursor
                current_text = self._get_cursor_text()
                if current_text and current_text != last_text:
                    # Found new response
                    self.last_response = current_text
                    self._save_response(current_text, agent_id)
                    
                    # Try to copy response if copy button region is defined
                    for name, region in self.agent_regions.items():
                        if agent_id is None or region.agent_id == agent_id:
                            if region.try_copy_response():
                                logger.info(f"Successfully copied response for agent {region.agent_id}")
                    
                    return True
                
                # Check agent region stability
                for name, region in self.agent_regions.items():
                    if agent_id is None or region.agent_id == agent_id:
                        if region.is_stable():
                            logger.info(f"Agent {region.agent_id or 'unknown'} response stabilized")
                            return True
                
                time.sleep(0.1)  # Check every 100ms
            
        except Exception as e:
            logger.error(f"Error collecting response: {e}")
            return False
    
    def _save_response(self, response: str, agent_id: Optional[str] = None) -> None:
        """Save response to file."""
        try:
            # Create timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            agent_prefix = f"agent_{agent_id}_" if agent_id else ""
            filename = f"{agent_prefix}response_{timestamp}.md"
            filepath = self.save_dir / filename
            
            # Save response
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response)
            
            self.response_count += 1
            logger.info(f"Saved response {self.response_count} to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving response: {e}")
    
    def get_saved_responses(self, agent_id: Optional[str] = None) -> List[Path]:
        """Get list of saved response files."""
        pattern = f"agent_{agent_id}_response_*.md" if agent_id else "response_*.md"
        return list(self.save_dir.glob(pattern))
    
    def get_latest_response(self, agent_id: Optional[str] = None) -> Optional[str]:
        """Get the most recent response content."""
        responses = self.get_saved_responses(agent_id)
        if not responses:
            return None
            
        latest = max(responses, key=lambda p: p.stat().st_mtime)
        try:
            with open(latest, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading latest response: {e}")
            return None
    
    def clear_responses(self, agent_id: Optional[str] = None) -> None:
        """Clear all saved responses."""
        for file in self.get_saved_responses(agent_id):
            try:
                file.unlink()
                logger.info(f"Deleted response file: {file}")
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")
        self.response_count = 0

def collect_response(timeout: int = 300, agent_id: Optional[str] = None) -> Optional[str]:
    """Helper function to collect a single response.
    
    Args:
        timeout: Maximum time to wait for response in seconds
        agent_id: Optional SWARM agent ID to monitor
        
    Returns:
        The collected response text, or None if timeout
    """
    collector = ResponseCollector()
    if collector.start_collecting(timeout, agent_id):
        return collector.get_latest_response(agent_id)
    return None 