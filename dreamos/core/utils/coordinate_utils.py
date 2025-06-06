"""
Coordinate Utilities

Provides shared coordinate transformation, validation, and management functions.
"""

import json
import logging
# Attempt to import pyautogui. This package requires an active display
# which may not be present in headless test environments. Provide a
# lightweight fallback so modules importing this file don't fail when
# pyautogui is unavailable.
try:
    import pyautogui  # type: ignore
except Exception:  # pragma: no cover - best effort fallback
    class _DummyPyAutoGUI:
        """Minimal stub implementing the small subset of pyautogui used here."""

        @staticmethod
        def size() -> tuple[int, int]:
            # Default to a standard HD resolution.
            return (1920, 1080)

    pyautogui = _DummyPyAutoGUI()  # type: ignore
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

logger = logging.getLogger('utils.coords')

def transform_coordinates(x: int, y: int) -> Tuple[int, int]:
    """Transform coordinates to valid screen space.
    
    Args:
        x: X coordinate (can be negative for right-edge offset)
        y: Y coordinate
        
    Returns:
        Tuple of (transformed_x, transformed_y) within screen bounds
    """
    # Get screen dimensions
    screen_width, screen_height = pyautogui.size()
    logger.debug(f"Screen dimensions: {screen_width}x{screen_height}")
    logger.debug(f"Input coordinates: ({x}, {y})")
    
    # Transform negative X (right-edge offset)
    if x < 0:
        x = screen_width + x
        logger.debug(f"Negative X transformed: {x} (distance from right)")
    
    # Clamp to screen bounds
    x = max(0, min(x, screen_width))
    y = max(0, min(y, screen_height))
    
    logger.debug(f"Transformed coordinates: ({x}, {y})")
    return x, y

def load_coordinates(config_path: Union[str, Path]) -> Dict:
    """Load coordinates from a JSON file.
    
    Args:
        config_path: Path to the coordinates config file
        
    Returns:
        Dictionary of coordinate data
    """
    try:
        config_path = Path(config_path)
        if not config_path.exists():
            logger.error(f"Coordinate file not found at {config_path}")
            return {}
            
        with open(config_path, 'r') as f:
            return json.load(f)
            
    except Exception as e:
        logger.error(f"Error loading coordinates from {config_path}: {e}")
        return {}

def validate_coordinates(coords: Dict) -> bool:
    """Validate coordinate data structure.
    
    Args:
        coords: Dictionary of coordinate data
        
    Returns:
        True if coordinates are valid
    """
    try:
        required_keys = {'input_box', 'copy_button'}
        for agent_id, agent_coords in coords.items():
            if not isinstance(agent_coords, dict):
                logger.error(f"Invalid coordinate format for {agent_id}")
                return False
                
            if not all(key in agent_coords for key in required_keys):
                logger.error(f"Missing required keys for {agent_id}")
                return False
                
            for key, value in agent_coords.items():
                if not isinstance(value, (list, tuple)) or len(value) != 2:
                    logger.error(f"Invalid coordinate format for {agent_id}.{key}")
                    return False
                    
        return True
        
    except Exception as e:
        logger.error(f"Error validating coordinates: {e}")
        return False

def save_coordinates(coords: Dict, config_path: Union[str, Path]) -> bool:
    """Save coordinates to a JSON file.
    
    Args:
        coords: Dictionary of coordinate data
        config_path: Path to save coordinates to
        
    Returns:
        True if coordinates were saved successfully
    """
    try:
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(coords, f, indent=2)
            
        return True
        
    except Exception as e:
        logger.error(f"Error saving coordinates to {config_path}: {e}")
        return False 