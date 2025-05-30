"""
Coordinate Manager Module

Manages agent coordinates and positions for UI automation.
"""

import logging
import json
import os
from typing import Dict, Optional, Tuple
from pathlib import Path
import pyautogui

logger = logging.getLogger('agent_control.coordinates')

class CoordinateManager:
    """Manages agent coordinates and positions."""
    
    def __init__(self):
        self.coordinates = {}
        self.coords_file = Path("runtime/config/cursor_agent_coords.json")
        self.coords_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_coordinates()
    
    def load_coordinates(self):
        """Load coordinates from file."""
        try:
            if self.coords_file.exists():
                with open(self.coords_file, "r") as f:
                    self.coordinates = json.load(f)
            else:
                self.coordinates = {}
                self.save_coordinates()
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            self.coordinates = {}
    
    def save_coordinates(self):
        """Save coordinates to file."""
        try:
            with open(self.coords_file, "w") as f:
                json.dump(self.coordinates, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving coordinates: {e}")
    
    def get_coordinates(self, agent_id: str) -> dict:
        """Get coordinates for an agent."""
        return self.coordinates.get(agent_id, {})
    
    def set_coordinates(self, agent_id: str, coords: dict):
        """Set coordinates for an agent."""
        self.coordinates[agent_id] = coords
        self.save_coordinates()
    
    def validate_coordinates(self, coords: dict) -> bool:
        """Validate coordinate data structure and values."""
        try:
            if not isinstance(coords, dict):
                return False
            
            required_fields = ["input_box", "initial_spot", "copy_button", "response_region"]
            for field in required_fields:
                if field not in coords:
                    return False
                
                if field == "response_region":
                    if not isinstance(coords[field], dict):
                        return False
                    if "top_left" not in coords[field] or "bottom_right" not in coords[field]:
                        return False
                    if not isinstance(coords[field]["top_left"], dict) or not isinstance(coords[field]["bottom_right"], dict):
                        return False
                    if "x" not in coords[field]["top_left"] or "y" not in coords[field]["top_left"]:
                        return False
                    if "x" not in coords[field]["bottom_right"] or "y" not in coords[field]["bottom_right"]:
                        return False
                else:
                    if not isinstance(coords[field], dict):
                        return False
                    if "x" not in coords[field] or "y" not in coords[field]:
                        return False
            
            # In test environment, allow any non-negative coordinates
            if os.getenv("TESTING"):
                for field in required_fields:
                    if field == "response_region":
                        for point in ["top_left", "bottom_right"]:
                            if coords[field][point]["x"] < 0 or coords[field][point]["y"] < 0:
                                return False
                    else:
                        if coords[field]["x"] < 0 or coords[field]["y"] < 0:
                            return False
            else:
                # In production, validate against screen dimensions
                screen_width, screen_height = pyautogui.size()
                for field in required_fields:
                    if field == "response_region":
                        for point in ["top_left", "bottom_right"]:
                            if not (0 <= coords[field][point]["x"] <= screen_width and 
                                   0 <= coords[field][point]["y"] <= screen_height):
                                return False
                    else:
                        if not (0 <= coords[field]["x"] <= screen_width and 
                               0 <= coords[field]["y"] <= screen_height):
                            return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating coordinates: {e}")
            return False
    
    def get_global_ui_coords(self) -> dict:
        """Get global UI coordinates."""
        return self.coordinates.get("global_ui", {})
    
    def set_global_ui_coords(self, coords: dict):
        """Set global UI coordinates."""
        self.coordinates["global_ui"] = coords
        self.save_coordinates()
    
    def clear_coordinates(self):
        """Clear all coordinates."""
        self.coordinates = {}
        self.save_coordinates()
        
    def get_message_coordinates(self, agent_id: str) -> Optional[Tuple[int, int]]:
        """Get message coordinates for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Tuple of (x, y) coordinates for messages or None if not found
        """
        coords = self.get_coordinates(agent_id)
        if coords:
            return (coords['message_x'], coords['message_y'])
        return None
        
    def get_agent_coordinates(self, agent_id: str) -> Optional[Tuple[int, int]]:
        """Get agent coordinates.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Tuple of (x, y) coordinates or None if not found
        """
        coords = self.get_coordinates(agent_id)
        if coords:
            return (coords['x'], coords['y'])
        return None 