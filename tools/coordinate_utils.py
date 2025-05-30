"""
Coordinate Utilities

Shared utilities for handling agent coordinates and regions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def load_coordinates(config_path: str) -> Dict:
    """Load agent coordinates from config file.
    
    Args:
        config_path: Path to coordinate configuration file
        
    Returns:
        Dictionary of agent coordinates or empty dict if error
    """
    try:
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                return json.load(f)
        logger.error(f"No coordinate file found at {config_path}")
        return {}
    except Exception as e:
        logger.error(f"Error loading coordinates: {e}")
        return {}

def validate_coordinates(coords: Dict) -> Tuple[bool, List[str]]:
    """Validate coordinate structure and bounds.
    
    Args:
        coords: Dictionary of agent coordinates
        
    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    errors = []
    
    # Get screen dimensions
    try:
        import pyautogui
        screen_width, screen_height = pyautogui.size()
    except ImportError:
        logger.warning("pyautogui not available, skipping bounds validation")
        screen_width = screen_height = float('inf')
    
    for agent_id, agent_coords in coords.items():
        # Check required fields
        required_points = ["initial_spot", "input_box", "copy_button", "response_region"]
        for point in required_points:
            if point not in agent_coords:
                errors.append(f"Agent {agent_id} missing {point}")
                continue
                
            # Validate point coordinates
            if point != "response_region":
                if not isinstance(agent_coords[point], dict):
                    errors.append(f"Agent {agent_id} {point} must be a dictionary")
                    continue
                    
                if not all(k in agent_coords[point] for k in ["x", "y"]):
                    errors.append(f"Agent {agent_id} {point} missing x,y coordinates")
                    continue
                    
                # Check bounds
                x = agent_coords[point]["x"]
                y = agent_coords[point]["y"]
                if x < 0 or x > screen_width or y < 0 or y > screen_height:
                    errors.append(f"Agent {agent_id} {point} out of bounds: ({x}, {y})")
                    
        # Validate response region
        if "response_region" in agent_coords:
            region = agent_coords["response_region"]
            if not isinstance(region, dict):
                errors.append(f"Agent {agent_id} response_region must be a dictionary")
            elif not all(k in region for k in ["top_left", "bottom_right"]):
                errors.append(f"Agent {agent_id} response_region missing corners")
            else:
                # Check region bounds
                x1 = region["top_left"]["x"]
                y1 = region["top_left"]["y"]
                x2 = region["bottom_right"]["x"]
                y2 = region["bottom_right"]["y"]
                
                if x1 < 0 or x1 > screen_width or y1 < 0 or y1 > screen_height:
                    errors.append(f"Agent {agent_id} response_region top_left out of bounds: ({x1}, {y1})")
                if x2 < 0 or x2 > screen_width or y2 < 0 or y2 > screen_height:
                    errors.append(f"Agent {agent_id} response_region bottom_right out of bounds: ({x2}, {y2})")
                if x2 <= x1 or y2 <= y1:
                    errors.append(f"Agent {agent_id} response_region has invalid dimensions")
    
    return len(errors) == 0, errors

def regions_overlap(region1: Dict, region2: Dict) -> bool:
    """Check if two regions overlap.
    
    Args:
        region1: First region dictionary with top_left and bottom_right
        region2: Second region dictionary with top_left and bottom_right
        
    Returns:
        True if regions overlap, False otherwise
    """
    if not all(k in region1 for k in ["top_left", "bottom_right"]):
        return False
    if not all(k in region2 for k in ["top_left", "bottom_right"]):
        return False
        
    # Get coordinates
    x1 = region1["top_left"]["x"]
    y1 = region1["top_left"]["y"]
    x2 = region1["bottom_right"]["x"]
    y2 = region1["bottom_right"]["y"]
    
    x3 = region2["top_left"]["x"]
    y3 = region2["top_left"]["y"]
    x4 = region2["bottom_right"]["x"]
    y4 = region2["bottom_right"]["y"]
    
    # Check for overlap
    return not (x2 < x3 or x4 < x1 or y2 < y3 or y4 < y1)

def calculate_overlap(region1: Dict, region2: Dict) -> Dict:
    """Calculate overlap between two regions.
    
    Args:
        region1: First region dictionary with top_left and bottom_right
        region2: Second region dictionary with top_left and bottom_right
        
    Returns:
        Dictionary with overlap area and percentage
    """
    # Get coordinates
    x1 = max(region1["top_left"]["x"], region2["top_left"]["x"])
    y1 = max(region1["top_left"]["y"], region2["top_left"]["y"])
    x2 = min(region1["bottom_right"]["x"], region2["bottom_right"]["x"])
    y2 = min(region1["bottom_right"]["y"], region2["bottom_right"]["y"])
    
    # Calculate areas
    overlap_area = max(0, (x2 - x1) * (y2 - y1))
    region1_area = (
        (region1["bottom_right"]["x"] - region1["top_left"]["x"]) *
        (region1["bottom_right"]["y"] - region1["top_left"]["y"])
    )
    
    return {
        "area": overlap_area,
        "percentage": (overlap_area / region1_area * 100) if region1_area > 0 else 0
    }

def highlight_overlap_regions(regions: List[Dict], color: Tuple[int, int, int] = (255, 0, 0)) -> List[Dict]:
    """Find and highlight overlapping regions.
    
    Args:
        regions: List of region dictionaries
        color: RGB color tuple for highlighting
        
    Returns:
        List of dictionaries with overlap information
    """
    overlaps = []
    for i, region1 in enumerate(regions):
        for region2 in regions[i+1:]:
            if regions_overlap(region1, region2):
                overlap = calculate_overlap(region1, region2)
                overlaps.append({
                    "region1": region1,
                    "region2": region2,
                    "overlap": overlap,
                    "color": color
                })
    return overlaps

def compare_layouts(layout1: Dict, layout2: Dict) -> Dict:
    """Compare two coordinate layouts and report differences.
    
    Args:
        layout1: First layout dictionary
        layout2: Second layout dictionary
        
    Returns:
        Dictionary of differences found
    """
    differences = {
        "added_agents": [],
        "removed_agents": [],
        "modified_regions": [],
        "drift_metrics": {}
    }
    
    # Find added/removed agents
    agents1 = set(layout1.keys())
    agents2 = set(layout2.keys())
    differences["added_agents"] = list(agents2 - agents1)
    differences["removed_agents"] = list(agents1 - agents2)
    
    # Compare common agents
    for agent in agents1 & agents2:
        coords1 = layout1[agent]
        coords2 = layout2[agent]
        
        # Check each region
        for region in ["initial_spot", "input_box", "copy_button", "response_region"]:
            if region in coords1 and region in coords2:
                if coords1[region] != coords2[region]:
                    differences["modified_regions"].append({
                        "agent": agent,
                        "region": region,
                        "old": coords1[region],
                        "new": coords2[region]
                    })
    
    # Calculate drift metrics
    if differences["modified_regions"]:
        total_drift = 0
        for mod in differences["modified_regions"]:
            if "x" in mod["old"] and "x" in mod["new"]:
                total_drift += abs(mod["new"]["x"] - mod["old"]["x"])
            if "y" in mod["old"] and "y" in mod["new"]:
                total_drift += abs(mod["new"]["y"] - mod["old"]["y"])
        differences["drift_metrics"]["total_drift"] = total_drift
        differences["drift_metrics"]["average_drift"] = total_drift / len(differences["modified_regions"])
    
    return differences 