"""
Coordinate Utilities

Helper functions for loading and validating UI coordinates.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union

logger = logging.getLogger("coordinate_utils")

def load_coordinates(path: Union[str, Path]) -> Dict:
    """Load coordinates from a JSON file.
    
    Args:
        path: Path to the coordinates JSON file
        
    Returns:
        Dict containing the loaded coordinates
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading coordinates from {path}: {e}")
        return {}

def validate_coordinates(coords: Dict) -> Tuple[bool, List[str]]:
    """Validate the structure and values of coordinate data.
    
    Args:
        coords: Dictionary of coordinate data to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(coords, dict):
        errors.append("Coordinates must be a dictionary")
        return False, errors
        
    for agent_id, agent_coords in coords.items():
        if not isinstance(agent_coords, dict):
            errors.append(f"Invalid coordinate format for {agent_id}")
            continue
            
        required_keys = {"input_box", "initial_spot", "copy_button"}
        missing_keys = required_keys - set(agent_coords.keys())
        if missing_keys:
            errors.append(f"Missing required keys for {agent_id}: {missing_keys}")
            continue
            
        for key in required_keys:
            if not isinstance(agent_coords[key], dict):
                errors.append(f"Invalid format for {key} in {agent_id}")
                continue
                
            if not all(k in agent_coords[key] for k in ("x", "y")):
                errors.append(f"Missing x/y coordinates for {key} in {agent_id}")
                continue
                
            try:
                x = int(agent_coords[key]["x"])
                y = int(agent_coords[key]["y"])
            except ValueError:
                errors.append(f"Non-integer coordinates for {key} in {agent_id}")
    
    return len(errors) == 0, errors 
