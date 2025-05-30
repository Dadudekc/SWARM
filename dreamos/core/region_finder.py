"""
Region Finder

Utility to help find screen coordinates for Cursor's response areas.
"""

import time
import logging
import pyautogui
import keyboard
from typing import Tuple, List, Optional
import json
from pathlib import Path

logger = logging.getLogger('region_finder')

class RegionFinder:
    """Helps find screen coordinates for UI regions."""
    
    def __init__(self, save_file: str = "agent_regions.json"):
        """Initialize the region finder.
        
        Args:
            save_file: File to save region coordinates
        """
        self.save_file = Path(save_file)
        self.regions = self._load_regions()
        self.current_region = None
        self.start_pos = None
        self.end_pos = None
        
    def _load_regions(self) -> dict:
        """Load saved regions from file."""
        if self.save_file.exists():
            try:
                with open(self.save_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading regions: {e}")
        return {}
    
    def _save_regions(self) -> None:
        """Save regions to file."""
        try:
            with open(self.save_file, 'w') as f:
                json.dump(self.regions, f, indent=2)
            logger.info(f"Saved regions to {self.save_file}")
        except Exception as e:
            logger.error(f"Error saving regions: {e}")
    
    def start_finding(self, region_name: str) -> None:
        """Start finding coordinates for a region.
        
        Args:
            region_name: Name of the region to find
        """
        print(f"\nFinding coordinates for region: {region_name}")
        print("1. Move mouse to top-left corner of the region")
        print("2. Press 's' to set start position")
        print("3. Move mouse to bottom-right corner")
        print("4. Press 'e' to set end position")
        print("5. Press 'q' to quit")
        
        self.current_region = region_name
        self.start_pos = None
        self.end_pos = None
        
        # Set up keyboard hooks
        keyboard.on_press_key('s', lambda _: self._set_start())
        keyboard.on_press_key('e', lambda _: self._set_end())
        keyboard.on_press_key('q', lambda _: self._quit())
        
        try:
            while True:
                if self.start_pos and self.end_pos:
                    # Calculate region
                    left = min(self.start_pos[0], self.end_pos[0])
                    top = min(self.start_pos[1], self.end_pos[1])
                    right = max(self.start_pos[0], self.end_pos[0])
                    bottom = max(self.start_pos[1], self.end_pos[1])
                    
                    # Save region
                    self.regions[region_name] = {
                        'left': left,
                        'top': top,
                        'right': right,
                        'bottom': bottom
                    }
                    self._save_regions()
                    
                    print(f"\nRegion saved: {region_name}")
                    print(f"Coordinates: ({left}, {top}, {right}, {bottom})")
                    break
                
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nRegion finding cancelled")
        finally:
            # Clean up keyboard hooks
            keyboard.unhook_all()
    
    def _set_start(self) -> None:
        """Set the start position."""
        self.start_pos = pyautogui.position()
        print(f"Start position set: {self.start_pos}")
    
    def _set_end(self) -> None:
        """Set the end position."""
        self.end_pos = pyautogui.position()
        print(f"End position set: {self.end_pos}")
    
    def _quit(self) -> None:
        """Quit region finding."""
        raise KeyboardInterrupt()
    
    def get_region(self, region_name: str) -> Optional[Tuple[int, int, int, int]]:
        """Get coordinates for a saved region.
        
        Args:
            region_name: Name of the region
            
        Returns:
            Tuple of (left, top, right, bottom) coordinates, or None if not found
        """
        if region_name in self.regions:
            r = self.regions[region_name]
            return (r['left'], r['top'], r['right'], r['bottom'])
        return None

def find_cursor_regions() -> None:
    """Interactive tool to find Cursor response regions."""
    finder = RegionFinder()
    
    print("\nCursor Region Finder - Agent 6")
    print("=============================")
    print("This tool will help you find the coordinates for Agent 6's response areas.")
    print("Follow the instructions for each region.")
    
    # Find main response area for Agent 6
    print("\nFirst, let's find Agent 6's main response area:")
    print("This is where my responses appear in the chat.")
    finder.start_finding("agent_6_main_response")
    
    # Find typing indicator for Agent 6
    print("\nNow, let's find Agent 6's typing indicator area:")
    print("This is where the 'typing...' indicator appears when I'm responding.")
    finder.start_finding("agent_6_typing_indicator")
    
    print("\nAll regions saved!")
    print("You can use these coordinates in your ResponseCollector.")
    print("\nTo use these regions:")
    print("1. Open Cursor")
    print("2. Make sure you're chatting with Agent 6")
    print("3. The coordinates will be saved in agent_regions.json")

if __name__ == "__main__":
    find_cursor_regions() 