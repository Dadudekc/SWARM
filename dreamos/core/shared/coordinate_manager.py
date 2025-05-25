"""
Coordinate Manager Module

Manages agent coordinates and positions for UI automation.
"""

import logging
import json
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger('agent_control.coordinates')

class CoordinateManager:
    """Manages agent coordinates and positions."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the coordinate manager.
        
        Args:
            config_path: Optional path to coordinate configuration file
        """
        self.config_path = config_path or os.path.join(os.getcwd(), "config", "coordinates.json")
        self.coordinates: Dict[str, Dict[str, int]] = {}
        self._load_coordinates()
        
    def _load_coordinates(self) -> None:
        """Load coordinates from configuration file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.coordinates = json.load(f)
                logger.info(f"Loaded coordinates for {len(self.coordinates)} agents")
            else:
                logger.warning(f"Coordinate configuration not found at {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            self.coordinates = {}
            
    def get_coordinates(self, agent_id: str) -> Optional[Dict[str, int]]:
        """Get coordinates for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Dictionary containing x, y coordinates or None if not found
        """
        return self.coordinates.get(agent_id)
        
    def set_coordinates(self, agent_id: str, x: int, y: int, message_x: int, message_y: int) -> None:
        """Set coordinates for an agent.
        
        Args:
            agent_id: ID of the agent
            x: X coordinate
            y: Y coordinate
            message_x: Message X coordinate
            message_y: Message Y coordinate
        """
        self.coordinates[agent_id] = {
            'x': x,
            'y': y,
            'message_x': message_x,
            'message_y': message_y
        }
        self._save_coordinates()
        
    def _save_coordinates(self) -> None:
        """Save coordinates to configuration file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.coordinates, f, indent=2)
            logger.info("Saved coordinates to configuration file")
        except Exception as e:
            logger.error(f"Error saving coordinates: {e}")
            
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