"""
Coordinate Manager Module

Handles coordinate management, validation, and transformation for UI automation.
Supports both standard and recovery operations.
"""

import logging
import json
from typing import Dict, Tuple, Optional, List
from pathlib import Path
import screeninfo

from .coordinate_utils import (
    validate_coordinates,
    has_duplicate_coordinates,
    regions_overlap,
    region_overlap,
    load_coordinates as util_load_coordinates,
)
from dreamos.core.utils.json_utils import load_json, save_json
from dreamos.core.utils.file_ops import ensure_dir
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.exceptions import FileOpsError

logger = logging.getLogger("shared.coordinate_manager")


class CoordinateManager:
    """Manages coordinates for UI automation."""

    def __init__(self, config_path: Optional[str] = None, recovery_mode: bool = False):
        """Initialize coordinate manager.

        Args:
            config_path: Optional path to coordinate configuration file
            recovery_mode: Whether to operate in recovery mode
        """
        self.logger = logging.getLogger("shared.coordinate_manager")
        self.config_path = config_path
        self.coords: Dict = {}
        self.monitors = []
        self.primary_monitor = None
        self.screen_width = 1920  # Default values
        self.screen_height = 1080
        self.recovery_mode = recovery_mode

        self._initialize_monitors()
        if config_path:
            self._load_config(config_path)

    def _initialize_monitors(self):
        """Initialize monitor information."""
        try:
            self.monitors = screeninfo.get_monitors()
            if not self.monitors:
                self.logger.warning("No monitors found")
                return
            self.primary_monitor = self.monitors[0]
            self.logger.debug(f"Found {len(self.monitors)} monitors")
        except Exception as e:
            self.logger.error(f"Error initializing monitors: {e}")
            self.monitors = []
            self.primary_monitor = None

    def _load_config(self, config_path: str):
        """Load coordinates from config file.

        Args:
            config_path: Path to configuration file
        """
        try:
            self.logger.debug("Loading coordinates from file")
            with open(config_path, "r") as f:
                raw_data = json.load(f)
                self.logger.debug(
                    f"Raw coordinate data: {json.dumps(raw_data, indent=2)}"
                )

                for agent_id, coords in raw_data.items():
                    transformed = self._transform_coordinate_dict(coords)
                    self.coords[agent_id] = transformed
                    self.logger.debug(f"Processed coordinates for {agent_id}")

                self.logger.info(f"Loaded coordinates for {len(self.coords)} agents")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.coords = {}

    def _transform_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Transform coordinates based on monitor setup.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Tuple of (transformed_x, transformed_y)
        """
        if not self.primary_monitor:
            return x, y

        # Transform coordinates based on primary monitor
        transformed_x = x + self.primary_monitor.x
        transformed_y = y + self.primary_monitor.y

        return transformed_x, transformed_y

    def _transform_coordinate_dict(self, coords: Dict) -> Dict:
        """Transform all coordinates in a dictionary.

        Args:
            coords: Dictionary of coordinates to transform

        Returns:
            Transformed coordinate dictionary
        """
        transformed = {}

        # Transform point coordinates
        for key in ["initial_spot", "input_box", "copy_button"]:
            if key in coords:
                x, y = self._transform_coordinates(coords[key]["x"], coords[key]["y"])
                transformed[key] = {"x": x, "y": y}

        # Transform region coordinates
        if "response_region" in coords:
            region = coords["response_region"]
            top_left = self._transform_coordinates(
                region["top_left"]["x"], region["top_left"]["y"]
            )
            bottom_right = self._transform_coordinates(
                region["bottom_right"]["x"], region["bottom_right"]["y"]
            )

            transformed["response_region"] = {
                "top_left": {"x": top_left[0], "y": top_left[1]},
                "bottom_right": {"x": bottom_right[0], "y": bottom_right[1]},
            }

        return transformed

    def validate_coordinates(self, coords: Dict) -> Tuple[bool, Optional[str]]:
        """Validate coordinate format and values.

        Args:
            coords: Dictionary of coordinates to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        return validate_coordinates(coords, self.screen_width, self.screen_height)

    def has_duplicate_coordinates(self, coords: Dict) -> bool:
        """Check if there are any duplicate coordinates.

        Args:
            coords: Dictionary of coordinates to check

        Returns:
            True if duplicates found
        """
        return has_duplicate_coordinates(coords)

    def check_region_overlap(self, region1: Dict, region2: Dict) -> bool:
        """Check if two regions overlap.

        Args:
            region1: First region
            region2: Second region

        Returns:
            True if regions overlap
        """
        return regions_overlap(region1, region2)

    def get_agent_coordinates(self, agent_id: str) -> Optional[Dict]:
        """Get coordinates for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary of coordinates or None if not found
        """
        return self.coords.get(agent_id)

    def get_response_region(self, agent_id: str) -> Optional[Dict]:
        """Get response region for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Response region coordinates or None if not found
        """
        coords = self.get_agent_coordinates(agent_id)
        return coords.get("response_region") if coords else None

    def get(self, agent_id, key):
        return tuple(self.coords[agent_id][key])

    def get_all(self):
        return self.coords

    def get_overlap(self, agent_a, agent_b, key="input_box"):
        a = self.get(agent_a, key)
        b = self.get(agent_b, key)
        return region_overlap(a, b)

    def has_coordinates(self, agent_id: str) -> bool:
        """Check if coordinates exist for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            bool: True if coordinates exist
        """
        return agent_id in self.coords

    def get_coordinates(self, agent_id: str) -> Optional[Dict]:
        """Get coordinates for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dict: Coordinates for the agent or None if not found
        """
        return self.coords.get(agent_id)

    def set_coordinates(self, agent_id: str, coordinates: Dict) -> None:
        """Set coordinates for an agent.

        Args:
            agent_id: ID of the agent
            coordinates: Dictionary of coordinates
        """
        self.coords[agent_id] = coordinates
        if self.config_path:
            self._save_config()

    def _save_config(self) -> None:
        """Save coordinates to config file."""
        try:
            ensure_dir(Path(self.config_path).parent)
            save_json(self.coords, self.config_path)
        except Exception as e:
            self.logger.error(f"Error saving coordinates: {e}")


def load_coordinates(config_path: str) -> Dict:
    """Load coordinates from a configuration file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Dictionary of coordinates

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    return util_load_coordinates(config_path)


def save_coordinates(coords: Dict, config_path: str) -> bool:
    """Save coordinates to a configuration file.

    Args:
        coords: Dictionary of coordinates to save
        config_path: Path to save the configuration file

    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        config_dir = Path(config_path).parent
        ensure_dir(config_dir)

        # Save coordinates
        with open(config_path, "w") as f:
            json.dump(coords, f, indent=2)

        logger.info(f"Saved coordinates to {config_path}")
        return True

    except Exception as e:
        logger.error(f"Error saving coordinates: {e}")
        return False


def get_coordinates(agent_id: str = None) -> dict:
    """
    Load and return stored cursor coordinates.
    If `agent_id` is provided, return only that agent's coords; otherwise return all.

    Args:
        agent_id: Optional agent ID to get coordinates for

    Returns:
        Dictionary of coordinates
    """
    coords_file = (
        Path(__file__).parent.parent.parent / "config" / "cursor_agent_coords.json"
    )
    if not coords_file.exists():
        logger.warning(f"Coordinates file not found: {coords_file}")
        return {}

    try:
        coords = load_json(coords_file)
        if agent_id:
            return coords.get(agent_id, {})
        return coords
    except Exception as e:
        logger.error(f"Error loading coordinates: {e}")
        return {}


def set_coordinates(agent_id: str, coordinates: dict) -> None:
    """
    Update coordinates for a specific agent.

    Args:
        agent_id: Agent ID to update coordinates for
        coordinates: New coordinates to set
    """
    coords_file = (
        Path(__file__).parent.parent.parent / "config" / "cursor_agent_coords.json"
    )
    try:
        # Load existing coordinates
        coords = load_json(coords_file) if coords_file.exists() else {}

        # Update coordinates for agent
        coords[agent_id] = coordinates

        # Save updated coordinates
        save_json(coords_file, coords)
        logger.info(f"Updated coordinates for agent {agent_id}")
    except Exception as e:
        logger.error(f"Error updating coordinates: {e}")
        raise
