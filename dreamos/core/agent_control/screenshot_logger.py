"""
Screenshot logging functionality for UI automation.

This module provides a class for tracking and managing debug screenshots
taken during UI automation operations.
"""

import time
import logging
from pathlib import Path
from typing import Optional, List, Dict
from PIL import Image
import pygetwindow as gw

logger = logging.getLogger('agent_control.screenshot_logger')

class ScreenshotLogger:
    """Tracks and manages debug screenshots for UI automation."""
    
    def __init__(self, agent_id: str, debug_dir: Optional[Path] = None):
        """Initialize screenshot logger.
        
        Args:
            agent_id: ID of the agent being monitored
            debug_dir: Optional custom debug directory
        """
        self.agent_id = agent_id
        self.debug_dir = debug_dir or Path("runtime/debug/screenshots")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Track screenshots for this session
        self.screenshots: List[Dict] = []
        
        # Create session directory
        self.session_dir = self.debug_dir / f"{agent_id}_{time.strftime('%Y%m%d_%H%M%S')}"
        self.session_dir.mkdir(exist_ok=True)
        
        logger.debug(f"Initialized screenshot logger for {agent_id}")
        logger.debug(f"Session directory: {self.session_dir}")
        
    def capture(self, name: str, region: Optional[tuple] = None) -> Optional[Path]:
        """Capture a screenshot and log its details.
        
        Args:
            name: Name for the screenshot
            region: Optional region to capture
            
        Returns:
            Path to saved screenshot if successful, None otherwise
        """
        try:
            # Get active window info
            win = gw.getActiveWindow()
            window_info = {
                "title": win.title if win else "No active window",
                "position": win.topleft if win else (0, 0),
                "size": win.size if win else (0, 0)
            }
            
            # Take screenshot
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            path = self.session_dir / filename
            
            screenshot = Image.grab(bbox=region)
            screenshot.save(path)
            
            # Log screenshot details
            screenshot_info = {
                "timestamp": timestamp,
                "name": name,
                "path": str(path),
                "window": window_info,
                "region": region
            }
            self.screenshots.append(screenshot_info)
            
            logger.debug(f"Captured screenshot: {path}")
            logger.debug(f"Window info: {window_info}")
            
            return path
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return None
            
    def get_screenshots(self, name: Optional[str] = None) -> List[Dict]:
        """Get list of captured screenshots.
        
        Args:
            name: Optional filter by screenshot name
            
        Returns:
            List of screenshot info dictionaries
        """
        if name:
            return [s for s in self.screenshots if s["name"] == name]
        return self.screenshots
        
    def get_latest_screenshot(self, name: Optional[str] = None) -> Optional[Dict]:
        """Get the most recent screenshot.
        
        Args:
            name: Optional filter by screenshot name
            
        Returns:
            Most recent screenshot info dictionary or None
        """
        screenshots = self.get_screenshots(name)
        return screenshots[-1] if screenshots else None
        
    def compare_screenshots(self, name1: str, name2: str) -> Optional[float]:
        """Compare two screenshots and return similarity score.
        
        Args:
            name1: Name of first screenshot
            name2: Name of second screenshot
            
        Returns:
            Similarity score (0-1) or None if comparison fails
        """
        try:
            shot1 = self.get_latest_screenshot(name1)
            shot2 = self.get_latest_screenshot(name2)
            
            if not shot1 or not shot2:
                return None
                
            # Load images
            img1 = Image.open(shot1["path"])
            img2 = Image.open(shot2["path"])
            
            # Ensure same size
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)
                
            # Calculate difference
            diff = Image.new('RGB', img1.size)
            for x in range(img1.width):
                for y in range(img1.height):
                    r1, g1, b1 = img1.getpixel((x, y))
                    r2, g2, b2 = img2.getpixel((x, y))
                    diff.putpixel((x, y), (
                        abs(r1 - r2),
                        abs(g1 - g2),
                        abs(b1 - b2)
                    ))
                    
            # Calculate similarity score
            total_pixels = img1.width * img1.height
            diff_pixels = sum(1 for x in range(img1.width) for y in range(img1.height)
                            if any(c > 30 for c in diff.getpixel((x, y))))
            similarity = 1 - (diff_pixels / total_pixels)
            
            logger.debug(f"Screenshot comparison: {name1} vs {name2}")
            logger.debug(f"Similarity score: {similarity:.2f}")
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {e}")
            return None
            
    def cleanup(self):
        """Clean up old screenshots."""
        try:
            # Keep only last 10 sessions
            sessions = sorted(self.debug_dir.glob(f"{self.agent_id}_*"))
            if len(sessions) > 10:
                for session in sessions[:-10]:
                    logger.debug(f"Removing old session: {session}")
                    for file in session.glob("*"):
                        file.unlink()
                    session.rmdir()
                    
        except Exception as e:
            logger.error(f"Error cleaning up screenshots: {e}") 
