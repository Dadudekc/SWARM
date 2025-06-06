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
import pygetwindow as gw
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
    "Agent-1", "Agent-2", "Agent-3", "Agent-4",
    "Agent-5", "Agent-6", "Agent-7", "Agent-8"
]

def get_window_info() -> Tuple[str, str]:
    """Get information about the currently active window.
    
    Returns:
        Tuple of (window_title, monitor_info)
    """
    try:
        win = gw.getActiveWindow()
        if win:
            title = win.title
            # Get monitor info
            x, y = win.left, win.top
            monitor = "Unknown"
            for m in gw.getAllMonitors():
                if m.left <= x < m.left + m.width and m.top <= y < m.top + m.height:
                    monitor = f"Monitor {m.name} ({m.width}x{m.height})"
                    break
            return title, monitor
    except Exception as e:
        logger.error(f"Error getting window info: {e}")
    return "Unknown", "Unknown"

def capture_point(agent_id: str, label: str) -> Dict:
    """Capture a coordinate point with window focus validation.
    
    Args:
        agent_id: ID of the agent
        label: Label for the point being captured
        
    Returns:
        Dictionary with coordinate and window information
    """
    pyautogui.alert(f"Click the {label} for {agent_id}, then press ENTER.")
    time.sleep(0.2)  # Small pause to let window focus settle
    
    pos = pyautogui.position()
    win_title, monitor = get_window_info()
    
    logger.info(f"{agent_id} {label}:")
    logger.info(f"  Position: ({pos.x}, {pos.y})")
    logger.info(f"  Window: {win_title}")
    logger.info(f"  Monitor: {monitor}")
    
    return {
        "x": pos.x,
        "y": pos.y,
        "window": win_title,
        "monitor": monitor
    }

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
        # Check input box coordinates
        input_box = (agent_coords["input_box"]["x"], agent_coords["input_box"]["y"])
        if input_box in seen:
            logger.error(f"Duplicate input box coordinates for {agent_id}!")
            return False
        seen.add(input_box)
        
        # Check copy button coordinates
        copy_button = (agent_coords["copy_button"]["x"], agent_coords["copy_button"]["y"])
        if copy_button in seen:
            logger.error(f"Duplicate copy button coordinates for {agent_id}!")
            return False
        seen.add(copy_button)
        
        # Check initial spot coordinates
        initial_spot = (agent_coords["initial_spot"]["x"], agent_coords["initial_spot"]["y"])
        if initial_spot in seen:
            logger.error(f"Duplicate initial spot coordinates for {agent_id}!")
            return False
        seen.add(initial_spot)
    
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
            
            # Capture initial spot
            coords[agent_id]["initial_spot"] = capture_point(agent_id, "initial spot")
            
            # Capture input box
            coords[agent_id]["input_box"] = capture_point(agent_id, "input box")
            
            # Capture copy button
            coords[agent_id]["copy_button"] = capture_point(agent_id, "copy button")
            
            # Optionally capture response region
            if pyautogui.confirm(
                f"Do you want to calibrate a response region for {agent_id}?",
                buttons=["Yes", "No"]
            ) == "Yes":
                logger.info(f"Capturing response region for {agent_id}")
                top_left = capture_point(agent_id, "response region top-left")
                bottom_right = capture_point(agent_id, "response region bottom-right")
                coords[agent_id]["response_region"] = {
                    "top_left": {"x": top_left["x"], "y": top_left["y"]},
                    "bottom_right": {"x": bottom_right["x"], "y": bottom_right["y"]}
                }
        
        # Validate coordinates
        is_valid, errors = validate_coordinates(coords)
        if not is_valid:
            logger.error("Coordinate validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            if not pyautogui.confirm(
                "Do you want to save the coordinates anyway?",
                buttons=["Yes", "No"]
            ) == "Yes":
                logger.info("Calibration cancelled")
                return
                
        # Validate uniqueness
        if not validate_unique_coordinates(coords):
            logger.error("Coordinate uniqueness validation failed!")
            if not pyautogui.confirm(
                "Do you want to save the coordinates anyway?",
                buttons=["Yes", "No"]
            ) == "Yes":
                logger.info("Calibration cancelled")
                return
        
        # Strip window/monitor info for final save
        for agent_id in coords:
            for label in ["initial_spot", "input_box", "copy_button"]:
                coords[agent_id][label] = {
                    "x": coords[agent_id][label]["x"],
                    "y": coords[agent_id][label]["y"]
                }
        
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