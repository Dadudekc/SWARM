"""
Coordinate Manager

Manages cursor coordinates for agent UI interaction.
"""

import logging
import json
from pathlib import Path
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger('coordinate_manager')

class CoordinateManager:
    """Manages cursor coordinates for agent UI interaction."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the coordinate manager.
        
        Args:
            config_path: Optional path to the coordinates config file.
                        Defaults to runtime/config/cursor_agent_coords.json
        """
        self.config_path = config_path or "D:/SWARM/Dream.OS/runtime/config/cursor_agent_coords.json"
        self.coordinates = self._load_coordinates()
        
    def _load_coordinates(self) -> Dict[str, Dict[str, Tuple[int, int]]]:
        """Load cursor coordinates from JSON file.
        
        Returns:
            Dictionary mapping agent IDs to their coordinate sets
        """
        try:
            config_path = Path(self.config_path)
            
            if not config_path.exists():
                logger.error(f"Coordinates file not found at {config_path}")
                return {}
                
            with open(config_path, 'r') as f:
                coords = json.load(f)
                
            # Convert nested coordinate dictionaries to tuples
            processed_coords = {}
            for agent_id, agent_coords in coords.items():
                if agent_id == "global_ui":
                    continue
                    
                processed_coords[agent_id] = {
                    "input_box": (agent_coords["input_box"]["x"], agent_coords["input_box"]["y"]),
                    "initial_spot": (agent_coords["initial_spot"]["x"], agent_coords["initial_spot"]["y"]),
                    "copy_button": (agent_coords["copy_button"]["x"], agent_coords["copy_button"]["y"])
                }
                
            logger.info(f"Loaded coordinates for {len(processed_coords)} agents")
            return processed_coords
            
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return {}
            
    def get_coordinates(self, agent_id: str) -> Optional[Dict[str, Tuple[int, int]]]:
        """Get coordinates for a specific agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dictionary of coordinates if found, None otherwise
        """
        return self.coordinates.get(agent_id)
        
    def list_agents(self) -> List[str]:
        """Get a list of available agents.
        
        Returns:
            List of agent IDs
        """
        return sorted(self.coordinates.keys()) 