"""
Coordinate Manager

Handles loading, validating and providing access to cursor coordinates.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .coordinate_utils import load_coordinates, validate_coordinates

logger = logging.getLogger("coordinate_manager")


class CoordinateManager:
    """Manage UI coordinate configuration."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """Initialize the manager and load coordinates."""
        if os.environ.get("PYTEST_CURRENT_TEST"):
            default_path = Path(__file__).resolve().parents[2] / "tests" / "config" / "test_agent_coords.json"
        else:
            default_path = Path(__file__).resolve().parents[2] / "runtime" / "config" / "cursor_agent_coords.json"

        self.config_file = Path(config_path) if config_path else default_path
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        self.raw_coordinates: Dict = {}
        self.coordinates: Dict[str, Dict[str, Tuple[int, int]]] = {}
        self.load_coordinates()

    # ------------------------------------------------------------------
    def load_coordinates(self) -> None:
        """Load coordinates from disk into memory."""
        try:
            if self.config_file.exists():
                self.raw_coordinates = load_coordinates(self.config_file)
            else:
                self.raw_coordinates = {}
                self.save_coordinates()

            if not self.raw_coordinates:
                logger.warning(f"No coordinates found at {self.config_file}")

            is_valid, errors = validate_coordinates(self.raw_coordinates)
            if not is_valid:
                for err in errors:
                    logger.warning(f"Validation error: {err}")

            self.coordinates = self._process_raw(self.raw_coordinates)
        except Exception as exc:
            logger.error(f"Error loading coordinates: {exc}")
            self.raw_coordinates = {}
            self.coordinates = {}

    # ------------------------------------------------------------------
    def save_coordinates(self) -> None:
        """Persist current coordinates to disk."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.raw_coordinates, f, indent=2)
        except Exception as exc:
            logger.error(f"Error saving coordinates: {exc}")

    # ------------------------------------------------------------------
    @staticmethod
    def _process_raw(coords: Dict) -> Dict[str, Dict[str, Tuple[int, int]]]:
        processed = {}
        for agent_id, agent_coords in coords.items():
            if agent_id == "global_ui":
                continue
            try:
                processed[agent_id] = {
                    "input_box": (agent_coords["input_box"]["x"], agent_coords["input_box"]["y"]),
                    "initial_spot": (agent_coords["initial_spot"]["x"], agent_coords["initial_spot"]["y"]),
                    "copy_button": (agent_coords["copy_button"]["x"], agent_coords["copy_button"]["y"]),
                }
            except Exception as exc:  # malformed entry
                logger.warning(f"Invalid coordinate entry for {agent_id}: {exc}")
        return processed

    # ------------------------------------------------------------------
    def get_coordinates(self, agent_id: str) -> Optional[Dict[str, Tuple[int, int]]]:
        """Return tuple based coordinates for an agent."""
        return self.coordinates.get(agent_id)

    def set_coordinates(self, agent_id: str, coords: Dict[str, Tuple[int, int]]) -> None:
        """Update coordinates for an agent and save them."""
        self.coordinates[agent_id] = coords
        self.raw_coordinates[agent_id] = {
            "input_box": {"x": coords["input_box"][0], "y": coords["input_box"][1]},
            "initial_spot": {"x": coords["initial_spot"][0], "y": coords["initial_spot"][1]},
            "copy_button": {"x": coords["copy_button"][0], "y": coords["copy_button"][1]},
        }
        self.save_coordinates()

    # Convenience helpers ------------------------------------------------
    def get_agent_coordinates(self, agent_id: str) -> Optional[Tuple[int, int]]:
        coords = self.get_coordinates(agent_id)
        if coords:
            return coords.get("initial_spot")
        return None

    def get_input_box_coordinates(self, agent_id: str) -> Optional[Tuple[int, int]]:
        coords = self.get_coordinates(agent_id)
        if coords:
            return coords.get("input_box")
        return None

    def get_copy_button_coordinates(self, agent_id: str) -> Optional[Tuple[int, int]]:
        coords = self.get_coordinates(agent_id)
        if coords:
            return coords.get("copy_button")
        return None

    def list_agents(self) -> List[str]:
        """Return list of agent identifiers."""
        return sorted(self.coordinates.keys())
