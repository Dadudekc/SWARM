"""
Coordinate Calibration Script

Calibrates UI coordinates for agent interactions with proper window focus handling.
"""

import json
import logging
import time
import os
from pathlib import Path
import pyautogui
import keyboard
from typing import Dict, Tuple, Optional

from dreamos.core.coordinate_utils import load_coordinates, validate_coordinates

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CONFIG_PATH = "config/cursor_agent_coords.json"
AGENT_LIST = [
    "Agent-5", "Agent-6", "Agent-7", "Agent-8"
]

def get_window_info() -> Tuple[str, str]:
    """Get information about the currently active window.
    
    Returns:
        Tuple of (window_title, monitor_info)
    """
    try:
        win = pyautogui.getActiveWindow()
        if win:
            title = win.title
            # Get monitor info
            x, y = win.left, win.top
            monitor = "Unknown"
            for m in pyautogui.getAllMonitors():
                if m.left <= x < m.left + m.width and m.top <= y < m.top + m.height:
                    monitor = f"Monitor {m.name} ({m.width}x{m.height})"
                    break
            return title, monitor
    except Exception as e:
        logger.error(f"Error getting window info: {e}")
    return "Unknown", "Unknown"

def capture_point(agent_id: str, label: str) -> Dict:
    """Capture a coordinate point.
    
    Args:
        agent_id: ID of the agent
        label: Label for the point being captured
        
    Returns:
        Dictionary with coordinate information
    """
    print(f"\nMove mouse to {agent_id}'s {label}")
    print("Press 'c' to capture or 'q' to quit")
    
    while True:
        if keyboard.is_pressed('c'):
            pos = pyautogui.position()
            logger.info(f"{agent_id} {label}:")
            logger.info(f"  Position: ({pos.x}, {pos.y})")
            time.sleep(0.3)  # Debounce
            return {"x": pos.x, "y": pos.y}
        elif keyboard.is_pressed('q'):
            raise KeyboardInterrupt()
        time.sleep(0.1)

def validate_unique_coordinates(coords: Dict) -> bool:
    """Validate that coordinates are unique across agents.
    
    Args:
        coords: Dictionary of agent coordinates
        
    Returns:
        True if coordinates are unique, False otherwise
    """
    # Check for duplicate coordinates
    seen = set()
    for agent_id, agent_coords in coords.items():
        if agent_id == "global_ui":
            continue
            
        # Check input box coordinates
        if "input_box" in agent_coords:
            input_box = (agent_coords["input_box"]["x"], agent_coords["input_box"]["y"])
            if input_box in seen:
                logger.error(f"Duplicate input box coordinates for {agent_id}!")
                return False
            seen.add(input_box)
        
        # Check copy button coordinates
        if "copy_button" in agent_coords:
            copy_button = (agent_coords["copy_button"]["x"], agent_coords["copy_button"]["y"])
            if copy_button in seen:
                logger.error(f"Duplicate copy button coordinates for {agent_id}!")
                return False
            seen.add(copy_button)
        
        # Check initial spot coordinates
        if "initial_spot" in agent_coords:
            initial_spot = (agent_coords["initial_spot"]["x"], agent_coords["initial_spot"]["y"])
            if initial_spot in seen:
                logger.error(f"Duplicate initial spot coordinates for {agent_id}!")
                return False
            seen.add(initial_spot)
            
        # Check response region coordinates
        if "response_region" in agent_coords:
            top_left = (agent_coords["response_region"]["top_left"]["x"], 
                       agent_coords["response_region"]["top_left"]["y"])
            bottom_right = (agent_coords["response_region"]["bottom_right"]["x"], 
                          agent_coords["response_region"]["bottom_right"]["y"])
            if top_left in seen or bottom_right in seen:
                logger.error(f"Duplicate response region coordinates for {agent_id}!")
                return False
            seen.add(top_left)
            seen.add(bottom_right)
    
    return True

def main():
    """Run the calibration process."""
    try:
        # Load existing coordinates if available
        coords = load_coordinates(CONFIG_PATH)
        if coords:
            logger.info(f"Loaded existing coordinates for {len(coords)} agents")
        else:
            coords = {}
            logger.info("No existing coordinates found, starting fresh")
        
        # Calibrate each agent
        for agent_id in AGENT_LIST:
            logger.info(f"\n--- Calibrating {agent_id} ---")
            coords[agent_id] = {}
            
            try:
                # Capture initial spot
                coords[agent_id]["initial_spot"] = capture_point(agent_id, "initial spot")
                
                # Capture input box
                coords[agent_id]["input_box"] = capture_point(agent_id, "input box")
                
                # Capture copy button
                coords[agent_id]["copy_button"] = capture_point(agent_id, "copy button")
                
                # Optionally capture response region
                print(f"\nDo you want to calibrate a response region for {agent_id}?")
                print("Press 'y' for yes, any other key for no")
                if keyboard.read_event(suppress=True).name == 'y':
                    logger.info(f"Capturing response region for {agent_id}")
                    print("Move to top-left corner and press 'c'")
                    top_left = capture_point(agent_id, "response region top-left")
                    print("Move to bottom-right corner and press 'c'")
                    bottom_right = capture_point(agent_id, "response region bottom-right")
                    coords[agent_id]["response_region"] = {
                        "top_left": top_left,
                        "bottom_right": bottom_right
                    }
            except KeyboardInterrupt:
                print(f"\nSkipping remaining points for {agent_id}")
                continue
        
        # Validate coordinates
        if not validate_unique_coordinates(coords):
            logger.error("Coordinate uniqueness validation failed!")
            print("\nDo you want to save the coordinates anyway?")
            print("Press 'y' for yes, any other key for no")
            if keyboard.read_event(suppress=True).name != 'y':
                logger.info("Calibration cancelled")
                return
        
        # Save coordinates
        config_path = Path(CONFIG_PATH)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup of existing file
        if config_path.exists():
            backup_path = config_path.with_suffix('.json.bak')
            config_path.rename(backup_path)
            logger.info(f"Created backup at {backup_path}")
        
        with open(config_path, "w") as f:
            json.dump(coords, f, indent=2)
        logger.info(f"Saved coordinates to {config_path}")
        
    except KeyboardInterrupt:
        logger.info("Calibration interrupted by user")
    except Exception as e:
        logger.error(f"Error during calibration: {e}")
        raise

if __name__ == "__main__":
    main() 