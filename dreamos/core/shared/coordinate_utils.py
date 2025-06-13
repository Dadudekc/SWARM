"""
Coordinate Utilities

Helper functions for loading and validating UI coordinates.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union, Optional

logger = logging.getLogger("coordinate_utils")


def load_coordinates(path: Union[str, Path]) -> Dict:
    """Load coordinates from a JSON file.

    Args:
        path: Path to the coordinates JSON file

    Returns:
        Dict containing the loaded coordinates
    """
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading coordinates from {path}: {e}")
        return {}


def validate_coordinates(
    coords: Dict, screen_width: int, screen_height: int
) -> Tuple[bool, Optional[str]]:
    """Validate coordinate format and values.

    Args:
        coords: Dictionary of coordinates to validate
        screen_width: Maximum allowed x coordinate
        screen_height: Maximum allowed y coordinate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check for required keys
        required_keys = ["initial_spot", "input_box", "copy_button"]
        for key in required_keys:
            if key not in coords:
                return False, f"Missing required coordinate: {key}"

            point = coords[key]
            if not isinstance(point, dict):
                return False, f"Invalid coordinate format for {key}: {point}"

            if "x" not in point or "y" not in point:
                return False, f"Missing x or y in {key} coordinates"

            try:
                x = int(point["x"])
                y = int(point["y"])
            except (ValueError, TypeError):
                return False, f"Invalid coordinate values in {key}: {point}"

            if x < 0 or x > screen_width or y < 0 or y > screen_height:
                return False, f"Coordinates out of bounds for {key}: ({x}, {y})"

        # Check for duplicates
        if has_duplicate_coordinates(coords):
            return False, "Duplicate coordinates found"

        return True, None

    except Exception as e:
        return False, f"Error validating coordinates: {e}"


def has_duplicate_coordinates(coords: Dict) -> bool:
    """Check if there are any duplicate coordinates in the dictionary.

    Args:
        coords: Dictionary of coordinates to check

    Returns:
        bool: True if duplicates found, False otherwise
    """
    try:
        # Convert all coordinate points to tuples for comparison
        points = []
        for key, value in coords.items():
            if isinstance(value, dict) and "x" in value and "y" in value:
                points.append((value["x"], value["y"]))

        # Check for duplicates
        return len(points) != len(set(points))
    except Exception:
        return False


def regions_overlap(region1: Dict, region2: Dict) -> bool:
    """Check if two regions overlap.

    Args:
        region1: First region with top_left and bottom_right points
        region2: Second region with top_left and bottom_right points

    Returns:
        True if regions overlap, False otherwise
    """
    try:
        # Get coordinates for first region
        x1 = region1["top_left"]["x"]
        y1 = region1["top_left"]["y"]
        x2 = region1["bottom_right"]["x"]
        y2 = region1["bottom_right"]["y"]

        # Get coordinates for second region
        x3 = region2["top_left"]["x"]
        y3 = region2["top_left"]["y"]
        x4 = region2["bottom_right"]["x"]
        y4 = region2["bottom_right"]["y"]

        # Check if one rectangle is to the left of the other
        if x2 < x3 or x4 < x1:
            return False

        # Check if one rectangle is above the other
        if y2 < y3 or y4 < y1:
            return False

        # If neither condition is true, rectangles overlap
        return True
    except Exception:
        return False


def region_overlap(region1: Dict, region2: Dict) -> bool:
    """Backward compatible wrapper around :func:`regions_overlap`."""
    return regions_overlap(region1, region2)
