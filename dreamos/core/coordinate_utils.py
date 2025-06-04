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


def regions_overlap(region1: Dict, region2: Dict) -> bool:
    """Check if two regions overlap."""
    if not all(k in region1 for k in ["top_left", "bottom_right"]):
        return False
    if not all(k in region2 for k in ["top_left", "bottom_right"]):
        return False

    x1 = region1["top_left"]["x"]
    y1 = region1["top_left"]["y"]
    x2 = region1["bottom_right"]["x"]
    y2 = region1["bottom_right"]["y"]

    x3 = region2["top_left"]["x"]
    y3 = region2["top_left"]["y"]
    x4 = region2["bottom_right"]["x"]
    y4 = region2["bottom_right"]["y"]

    return not (x2 < x3 or x4 < x1 or y2 < y3 or y4 < y1)


def calculate_overlap(region1: Dict, region2: Dict) -> Dict:
    """Calculate overlap between two regions."""
    x1 = max(region1["top_left"]["x"], region2["top_left"]["x"])
    y1 = max(region1["top_left"]["y"], region2["top_left"]["y"])
    x2 = min(region1["bottom_right"]["x"], region2["bottom_right"]["x"])
    y2 = min(region1["bottom_right"]["y"], region2["bottom_right"]["y"])

    overlap_area = max(0, (x2 - x1) * (y2 - y1))
    region1_area = (
        (region1["bottom_right"]["x"] - region1["top_left"]["x"]) *
        (region1["bottom_right"]["y"] - region1["top_left"]["y"])
    )

    return {
        "area": overlap_area,
        "percentage": (overlap_area / region1_area * 100) if region1_area > 0 else 0,
    }


def highlight_overlap_regions(
    regions: List[Dict], color: Tuple[int, int, int] = (255, 0, 0)
) -> List[Dict]:
    """Find and highlight overlapping regions."""
    overlaps = []
    for i, region1 in enumerate(regions):
        for region2 in regions[i + 1 :]:
            if regions_overlap(region1, region2):
                overlap = calculate_overlap(region1, region2)
                overlaps.append({
                    "region1": region1,
                    "region2": region2,
                    "overlap": overlap,
                    "color": color,
                })
    return overlaps


def compare_layouts(layout1: Dict, layout2: Dict) -> Dict:
    """Compare two coordinate layouts and report differences."""
    differences = {
        "added_agents": [],
        "removed_agents": [],
        "modified_regions": [],
        "drift_metrics": {},
    }

    agents1 = set(layout1.keys())
    agents2 = set(layout2.keys())
    differences["added_agents"] = list(agents2 - agents1)
    differences["removed_agents"] = list(agents1 - agents2)

    for agent in agents1 & agents2:
        coords1 = layout1[agent]
        coords2 = layout2[agent]
        for region in ["initial_spot", "input_box", "copy_button", "response_region"]:
            if region in coords1 and region in coords2:
                if coords1[region] != coords2[region]:
                    differences["modified_regions"].append({
                        "agent": agent,
                        "region": region,
                        "old": coords1[region],
                        "new": coords2[region],
                    })

    if differences["modified_regions"]:
        total_drift = 0
        for mod in differences["modified_regions"]:
            if "x" in mod["old"] and "x" in mod["new"]:
                total_drift += abs(mod["new"]["x"] - mod["old"]["x"])
            if "y" in mod["old"] and "y" in mod["new"]:
                total_drift += abs(mod["new"]["y"] - mod["old"]["y"])
        differences["drift_metrics"]["total_drift"] = total_drift
        differences["drift_metrics"]["average_drift"] = (
            total_drift / len(differences["modified_regions"])
        )

    return differences
