"""
Coordinate Utilities

Utility functions for loading and validating coordinate data.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union

logger = logging.getLogger(__name__)

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

def validate_coordinates(coords: Dict) -> Tuple[bool, List[str]]:
    """Validate coordinate data structure and values.
    
    Args:
        coords: Dictionary of coordinate data
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(coords, dict):
        errors.append("Coordinates must be a dictionary")
        return False, errors
        
    for agent_id, agent_coords in coords.items():
        if not isinstance(agent_coords, dict):
            errors.append(f"Agent {agent_id} coordinates must be a dictionary")
            continue
            
        required_fields = ["input_box", "initial_spot", "copy_button"]
        for field in required_fields:
            if field not in agent_coords:
                errors.append(f"Agent {agent_id} missing required field: {field}")
                continue
                
            if not isinstance(agent_coords[field], dict):
                errors.append(f"Agent {agent_id} {field} must be a dictionary")
                continue
                
            if "x" not in agent_coords[field] or "y" not in agent_coords[field]:
                errors.append(f"Agent {agent_id} {field} missing x or y coordinate")
                continue
                
            try:
                x = int(agent_coords[field]["x"])
                y = int(agent_coords[field]["y"])
                if not isinstance(x, int) or not isinstance(y, int):
                    errors.append(f"Agent {agent_id} {field} coordinates must be integers")
            except ValueError:
                errors.append(f"Agent {agent_id} {field} coordinates must be integers")
                
    return len(errors) == 0, errors 