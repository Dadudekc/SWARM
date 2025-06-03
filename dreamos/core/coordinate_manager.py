"""
Coordinate Manager

Manages cursor coordinates for agent UI interaction.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Tuple, Optional, List

from .coordinate_utils import load_coordinates, validate_coordinates

logger = logging.getLogger('coordinate_manager')

class CoordinateManager:
    """Manages cursor coordinates for agent UI interaction."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the coordinate manager.
        
        Args:
            config_path: Optional path to the coordinates config file.
                        Defaults to runtime/config/cursor_agent_coords.json
        """
        # Use test-specific file in test environment
        if os.environ.get('PYTEST_CURRENT_TEST'):
            self.config_path = config_path or str(Path(__file__).parent.parent.parent / "tests" / "config" / "test_agent_coords.json")
        else:
            self.config_path = config_path or "D:/SWARM/Dream.OS/runtime/config/cursor_agent_coords.json"
            
        self.coordinates = self._load_coordinates()
        
    def _load_coordinates(self) -> Dict[str, Dict[str, Tuple[int, int]]]:
        """Load cursor coordinates from JSON file.
        
        Returns:
            Dictionary mapping agent IDs to their coordinate sets
        """
        try:
            coords = load_coordinates(self.config_path)
            if not coords:
                logger.error(f"Failed to load coordinates from {self.config_path}")
                return {}
                
            # Validate coordinates
            is_valid, errors = validate_coordinates(coords)
            if not is_valid:
                logger.warning("Coordinate validation errors:")
                for error in errors:
                    logger.warning(f"  - {error}")
            
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