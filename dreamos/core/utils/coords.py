"""
Coordinate Utilities

Provides shared coordinate transformation and validation functions.
"""

import logging
import pyautogui
from typing import Tuple

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

def is_valid_coordinate(x: int, y: int) -> bool:
    """Check if coordinates are within valid screen bounds.
    
    Args:
        x: X coordinate
        y: Y coordinate
        
    Returns:
        True if coordinates are valid, False otherwise
    """
    screen_width, screen_height = pyautogui.size()
    return (0 <= x <= screen_width) and (0 <= y <= screen_height) 