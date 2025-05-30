"""
Coordinate Transformer Module

Handles coordinate transformation between monitor and screen space.
"""

import logging
import pyautogui
from typing import Dict, Tuple, Optional

logger = logging.getLogger('agent_control.coordinate_transformer')

class CoordinateTransformer:
    """Transforms coordinates between monitor and screen space."""
    
    def __init__(self, transform_debug: bool = False):
        """Initialize coordinate transformer.
        
        Args:
            transform_debug: Whether to enable debug logging
        """
        self.transform_debug = transform_debug
        try:
            self.screen_width, self.screen_height = pyautogui.size()
            if self.screen_width == 0 or self.screen_height == 0:
                logger.warning("Invalid screen dimensions detected, using default values")
                self.screen_width = 1920
                self.screen_height = 1080
        except Exception as e:
            logger.warning(f"Failed to get screen dimensions: {e}, using default values")
            self.screen_width = 1920
            self.screen_height = 1080
            
        self.monitors = self._get_monitors()
        
    def _get_monitors(self) -> list:
        """Get list of monitors.
        
        Returns:
            List of monitor information
        """
        try:
            from screeninfo import get_monitors
            return get_monitors()
        except ImportError:
            logger.warning("screeninfo not available - using fallback coordinate transformation")
            return []
            
    def transform_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Transform coordinates from monitor space to screen space.
        
        Args:
            x: X coordinate in monitor space
            y: Y coordinate in monitor space
            
        Returns:
            Tuple of (x, y) coordinates in screen space
        """
        try:
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Raw coordinates: ({x}, {y})")
            
            # Find the monitor that contains these coordinates
            monitor_offset = 0
            for monitor in self.monitors:
                if self.transform_debug:
                    logger.debug(f"[TRANSFORM] Checking monitor: x={monitor.x}, width={monitor.width}")
                
                # Check if coordinates are within this monitor's bounds
                if (monitor.x <= x < monitor.x + monitor.width and 
                    monitor.y <= y < monitor.y + monitor.height):
                    monitor_offset = monitor.x
                    if self.transform_debug:
                        logger.debug(f"[TRANSFORM] Found monitor match: x={monitor.x}")
                    break
            
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Using monitor offset: {monitor_offset}")
            
            # Transform coordinates
            screen_x = x - monitor_offset
            screen_y = y
            
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Transformed to: ({screen_x}, {screen_y})")
            
            # Ensure coordinates are within screen bounds
            screen_x = max(0, min(screen_x, self.screen_width))
            screen_y = max(0, min(screen_y, self.screen_height))
            
            if self.transform_debug:
                logger.debug(f"[TRANSFORM] Final coordinates: ({screen_x}, {screen_y})")
            
            return screen_x, screen_y
            
        except Exception as e:
            logger.error(f"Error transforming coordinates: {e}")
            return x, y  # Return original coordinates on error
            
    def transform_coordinate_dict(self, coords: Dict) -> Dict:
        """Transform coordinates in a dictionary from monitor space to screen space.
        
        Args:
            coords: Dictionary containing coordinate information
            
        Returns:
            Dictionary with transformed coordinates
        """
        try:
            transformed = {}
            
            # Store original coordinates
            transformed['original'] = coords.copy()
            
            # Transform initial spot
            if 'initial_spot' in coords:
                x, y = coords['initial_spot']['x'], coords['initial_spot']['y']
                screen_x, screen_y = self.transform_coordinates(x, y)
                transformed['x'] = screen_x
                transformed['y'] = screen_y
            
            # Transform input box
            if 'input_box' in coords:
                x, y = coords['input_box']['x'], coords['input_box']['y']
                screen_x, screen_y = self.transform_coordinates(x, y)
                # Ensure input box is to the right of initial spot
                if 'x' in transformed and screen_x <= transformed['x']:
                    screen_x = transformed['x'] + 20  # Add offset to ensure it's to the right
                transformed['message_x'] = screen_x
                transformed['message_y'] = screen_y
            
            # Transform copy button
            if 'copy_button' in coords:
                x, y = coords['copy_button']['x'], coords['copy_button']['y']
                screen_x, screen_y = self.transform_coordinates(x, y)
                # Ensure copy button is to the right of input box
                if 'message_x' in transformed and screen_x <= transformed['message_x']:
                    screen_x = transformed['message_x'] + 20  # Add offset to ensure it's to the right
                transformed['copy_x'] = screen_x
                transformed['copy_y'] = screen_y
            
            # Transform response region
            if 'response_region' in coords:
                region = coords['response_region']
                top_left = region['top_left']
                bottom_right = region['bottom_right']
                
                # Transform top left
                tl_x, tl_y = self.transform_coordinates(top_left['x'], top_left['y'])
                
                # Transform bottom right
                br_x, br_y = self.transform_coordinates(bottom_right['x'], bottom_right['y'])
                
                # Ensure response region is properly positioned
                if 'message_x' in transformed:
                    # Align response region with input box
                    tl_x = transformed['message_x']
                    br_x = tl_x + (br_x - tl_x)  # Maintain width
                
                transformed['response_region'] = {
                    'top_left': {'x': tl_x, 'y': tl_y},
                    'bottom_right': {'x': br_x, 'y': br_y}
                }
            
            if self.transform_debug:
                logger.debug("Transformed coordinates:")
                logger.debug(f"  original: {transformed}")
                logger.debug(f"  response_region: {transformed.get('response_region', {})}")
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming coordinate dictionary: {e}")
            return coords  # Return original coordinates on error 