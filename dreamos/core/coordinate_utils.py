"""Coordinate Utilities

Shared helpers for loading, validating and comparing UI coordinate layouts.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Union


logger = logging.getLogger(__name__)


def load_coordinates(config_path: Union[str, Path]) -> Dict:
    """Load agent coordinates from a JSON file.

    Args:
        config_path: Path to the coordinate configuration file.

    Returns:
        Dictionary of agent coordinates or an empty dict on failure.
    """

    try:
        path = Path(config_path)
        if not path.exists():
            logger.error(f"No coordinate file found at {config_path}")
            return {}

        with path.open("r") as f:
            return json.load(f)
    except Exception as exc:  # pragma: no cover - log and return empty
        logger.error(f"Error loading coordinates: {exc}")
        return {}


def validate_coordinates(coords: Dict) -> Tuple[bool, List[str]]:
    """Validate coordinate structure and bounds.

    Args:
        coords: Dictionary of agent coordinates.

    Returns:
        Tuple of ``(is_valid, list_of_errors)``.
    """

    errors: List[str] = []

    # Determine screen bounds if possible
    try:
        import pyautogui  # type: ignore

        screen_width, screen_height = pyautogui.size()
    except Exception:  # pragma: no cover - environment may not have pyautogui
        logger.warning("pyautogui not available, skipping bounds validation")
        screen_width = screen_height = float("inf")

    for agent_id, agent_coords in coords.items():
        required_points = ["initial_spot", "input_box", "copy_button", "response_region"]
        for point in required_points:
            if point not in agent_coords:
                errors.append(f"Agent {agent_id} missing {point}")
                continue

            if point != "response_region":
                if not isinstance(agent_coords[point], dict):
                    errors.append(f"Agent {agent_id} {point} must be a dictionary")
                    continue

                if not all(k in agent_coords[point] for k in ("x", "y")):
                    errors.append(f"Agent {agent_id} {point} missing x,y coordinates")
                    continue

                x = agent_coords[point]["x"]
                y = agent_coords[point]["y"]
                if x < 0 or x > screen_width or y < 0 or y > screen_height:
                    errors.append(f"Agent {agent_id} {point} out of bounds: ({x}, {y})")

        if "response_region" in agent_coords:
            region = agent_coords["response_region"]
            if not isinstance(region, dict):
                errors.append(f"Agent {agent_id} response_region must be a dictionary")
            elif not all(k in region for k in ("top_left", "bottom_right")):
                errors.append(f"Agent {agent_id} response_region missing corners")
            else:
                x1 = region["top_left"]["x"]
                y1 = region["top_left"]["y"]
                x2 = region["bottom_right"]["x"]
                y2 = region["bottom_right"]["y"]

                if x1 < 0 or x1 > screen_width or y1 < 0 or y1 > screen_height:
                    errors.append(
                        f"Agent {agent_id} response_region top_left out of bounds: ({x1}, {y1})"
                    )
                if x2 < 0 or x2 > screen_width or y2 < 0 or y2 > screen_height:
                    errors.append(
                        f"Agent {agent_id} response_region bottom_right out of bounds: ({x2}, {y2})"
                    )
                if x2 <= x1 or y2 <= y1:
                    errors.append(f"Agent {agent_id} response_region has invalid dimensions")

    return len(errors) == 0, errors


def regions_overlap(region1: Dict, region2: Dict) -> bool:
    """Check if two regions overlap."""

    if not all(k in region1 for k in ("top_left", "bottom_right")):
        return False
    if not all(k in region2 for k in ("top_left", "bottom_right")):
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


def highlight_overlap_regions(regions: List[Dict], color: Tuple[int, int, int] = (255, 0, 0)) -> List[Dict]:
    """Find and describe overlaps between regions."""

    overlaps: List[Dict] = []
    for i, region1 in enumerate(regions):
        for region2 in regions[i + 1:]:
            if regions_overlap(region1, region2):
                overlap = calculate_overlap(region1, region2)
                overlaps.append(
                    {
                        "region1": region1,
                        "region2": region2,
                        "overlap": overlap,
                        "color": color,
                    }
                )
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
            if region in coords1 and region in coords2 and coords1[region] != coords2[region]:
                differences["modified_regions"].append(
                    {
                        "agent": agent,
                        "region": region,
                        "old": coords1[region],
                        "new": coords2[region],
                    }
                )

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

