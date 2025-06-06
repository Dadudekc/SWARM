"""Coordinate transformation utilities."""

import pyautogui
from typing import Tuple

def transform_coordinates(x: int, y: int) -> Tuple[int, int]:
    """Transform coordinates based on screen dimensions.
    
    Args:
        x: X coordinate (0 to screen_width, or negative for right-edge offset)
        y: Y coordinate (0 to screen_height)
        
    Returns:
        Tuple of (transformed_x, transformed_y)
    """
    screen_width, screen_height = pyautogui.size()
    
    # Handle negative x coordinates (right-edge offset)
    if x < 0:
        x = screen_width + x
    
    # Ensure coordinates are within screen bounds
    x = max(0, min(x, screen_width))
    y = max(0, min(y, screen_height))
    
    return x, y 