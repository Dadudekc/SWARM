"""
Coordinate Calibrator

Manages UI coordinate calibration for agent interactions.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from ..shared.coordinate_utils import load_coordinates

logger = logging.getLogger("coordinate_calibrator")


class CoordinateCalibrator:
    """Manages UI coordinate calibration for agent interactions."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the coordinate calibrator.

        Args:
            config_path: Optional path to coordinate configuration file
        """
        self.config_path = config_path or str(
            Path(__file__).parent / "coordinates.json"
        )
        self.coordinates: Dict[str, Dict[str, Any]] = {}
        self.load_coordinates()

    def load_coordinates(self) -> None:
        """Load coordinates from configuration file."""
        try:
            if Path(self.config_path).exists():
                self.coordinates = load_coordinates(self.config_path)
                logger.info(f"Loaded coordinates for {len(self.coordinates)} agents")
            else:
                logger.warning(
                    f"Coordinate configuration not found at {self.config_path}"
                )
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            self.coordinates = {}

    def save_coordinates(self) -> None:
        """Save coordinates to configuration file."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self.coordinates, f, indent=2)
            logger.info(f"Saved coordinates for {len(self.coordinates)} agents")
        except Exception as e:
            logger.error(f"Error saving coordinates: {e}")

    def get_coordinates(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get coordinates for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary of coordinates or None if not found
        """
        return self.coordinates.get(agent_id)

    def update_coordinates(self, agent_id: str, coordinates: Dict[str, Any]) -> None:
        """Update coordinates for an agent.

        Args:
            agent_id: ID of the agent
            coordinates: New coordinates
        """
        self.coordinates[agent_id] = coordinates
        self.save_coordinates()

    def calibrate_agent(
        self,
        agent_id: str,
        initial_spot: Tuple[int, int],
        input_box: Tuple[int, int],
        copy_button: Tuple[int, int],
        response_region: Optional[Dict[str, Dict[str, int]]] = None,
    ) -> None:
        """Calibrate coordinates for an agent.

        Args:
            agent_id: ID of the agent
            initial_spot: (x, y) coordinates of initial spot
            input_box: (x, y) coordinates of input box
            copy_button: (x, y) coordinates of copy button
            response_region: Optional response region coordinates
        """
        coordinates = {
            "initial_spot": {"x": initial_spot[0], "y": initial_spot[1]},
            "input_box": {"x": input_box[0], "y": input_box[1]},
            "copy_button": {"x": copy_button[0], "y": copy_button[1]},
        }

        if response_region:
            coordinates["response_region"] = response_region

        self.update_coordinates(agent_id, coordinates)
        logger.info(f"Calibrated coordinates for {agent_id}")
