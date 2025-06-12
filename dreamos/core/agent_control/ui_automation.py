"""
UI Automation Module

Handles UI automation tasks using PyAutoGUI.
"""

import json
import logging
import signal
import threading
import time
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import keyboard
import pyautogui
import pygetwindow as gw
import pytesseract
import screeninfo
from PIL import Image
from screeninfo import get_monitors

from .cursor_controller import CursorController
from .response_capture import ResponseCapture
from .screenshot_logger import ScreenshotLogger
from .timing import (
    COPY_BUTTON_DELAY,
    DEBUG_SCREENSHOT_DELAY,
    FOCUS_ESTABLISH_DELAY,
    MESSAGE_SEND_DELAY,
    RESPONSE_CAPTURE_DELAY,
    TEXT_CLEAR_DELAY,
    TEXT_DELETE_DELAY,
    TYPING_COMPLETE_DELAY,
    TYPING_INTERVAL,
    WINDOW_ACTIVATION_DELAY,
)
from ..shared.coordinate_manager import (
    CoordinateManager,
    load_coordinates,
    save_coordinates,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
MESSAGE_SEND_DELAY = 1.0
CALIBRATION_DELAY = 0.5
SCREENSHOT_DELAY = 0.2


class UIAutomation:
    """UI automation class for handling screen interactions."""

    def __init__(self):
        """Initialize UI automation."""
        self.coords = {}
        self.calibrating = False
        self.screenshot_loggers = {}
        self.coordinate_manager = CoordinateManager()
        self.logger = logging.getLogger(__name__)

    def _get_screen_resolution(self) -> Tuple[int, int]:
        """Get screen resolution.

        Returns:
            Tuple of (width, height)
        """
        try:
            width, height = pyautogui.size()
            return width, height
        except Exception as e:
            self.logger.error(f"Error getting screen resolution: {e}")
            return 1920, 1080  # Default fallback

    def _is_coordinate_valid(self, x: int, y: int) -> bool:
        """Check if coordinate is valid.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            bool: True if valid
        """
        width, height = self._get_screen_resolution()
        return 0 <= x < width and 0 <= y < height

    def _move_to_coordinate(self, x: int, y: int) -> bool:
        """Move cursor to coordinate.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            bool: True if successful
        """
        try:
            if not self._is_coordinate_valid(x, y):
                return False
            pyautogui.moveTo(x, y)
            return True
        except Exception as e:
            self.logger.error(f"Error moving cursor: {e}")
            return False

    def _click_at_coordinate(self, x: int, y: int) -> bool:
        """Click at coordinate.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            bool: True if successful
        """
        try:
            if not self._is_coordinate_valid(x, y):
                return False
            pyautogui.click(x, y)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking: {e}")
            return False

    def _type_text(self, text: str) -> bool:
        """Type text.

        Args:
            text: Text to type

        Returns:
            bool: True if successful
        """
        try:
            pyautogui.write(text)
            return True
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")
            return False

    def _clear_text(self) -> bool:
        """Clear text field.

        Returns:
            bool: True if successful
        """
        try:
            pyautogui.hotkey("ctrl", "a")
            pyautogui.press("backspace")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing text: {e}")
            return False

    def _delete_text(self, length: int) -> bool:
        """Delete text.

        Args:
            length: Number of characters to delete

        Returns:
            bool: True if successful
        """
        try:
            for _ in range(length):
                pyautogui.press("backspace")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting text: {e}")
            return False

    def _wait_for_delay(self, delay: float) -> None:
        """Wait for specified delay.

        Args:
            delay: Delay in seconds
        """
        time.sleep(delay)

    def _capture_region(
        self, x: int, y: int, width: int, height: int
    ) -> Optional[Image.Image]:
        """Capture screen region.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Region width
            height: Region height

        Returns:
            Screenshot image or None if failed
        """
        try:
            return pyautogui.screenshot(region=(x, y, width, height))
        except Exception as e:
            self.logger.error(f"Error capturing region: {e}")
            return None

    def _get_text_from_region(self, x: int, y: int, width: int, height: int) -> str:
        """Get text from screen region.

        Args:
            x: X coordinate
            y: Y coordinate
            width: Region width
            height: Region height

        Returns:
            Extracted text
        """
        try:
            screenshot = self._capture_region(x, y, width, height)
            if screenshot:
                return pytesseract.image_to_string(screenshot)
            return ""
        except Exception as e:
            self.logger.error(f"Error getting text from region: {e}")
            return ""

    def _handle_interrupt(self, signum, frame):
        """Handle keyboard interrupt gracefully."""
        self.logger.info("Received interrupt signal, cleaning up...")
        self.cleanup()
        raise KeyboardInterrupt()

    def _cleanup_calibration(self):
        """Clean up calibration resources."""
        self.logger.debug("Cleaning up calibration resources")
        self.calibrating = False
        self.current_step = 0
        self.points = []

        if (
            self.calibration_thread
            and self.calibration_thread.is_alive()
            and threading.current_thread() != self.calibration_thread
        ):
            try:
                self.calibration_thread.join(timeout=1.0)
            except Exception as e:
                self.logger.error(f"Error joining calibration thread: {e}")

    def _validate_coordinates(self, coords: Dict) -> bool:
        """Validate coordinate format and values.

        Args:
            coords: Dictionary of coordinates to validate

        Returns:
            bool: True if valid, False otherwise
        """
        try:
            self.coord_manager = CoordinateManager(coords)
            return True
        except Exception as e:
            self.logger.error(f"Invalid coordinates: {e}")
            return False

    def _has_duplicate_coordinates(self, coords: Dict) -> bool:
        """Check if there are any duplicate coordinates.

        Args:
            coords: Dictionary of coordinates to check

        Returns:
            bool: True if duplicates found
        """
        return self.coord_manager.has_duplicate_coordinates(coords)

    def _check_region_overlap(self, region1: Dict, region2: Dict) -> bool:
        """Check if two regions overlap.

        Args:
            region1: First region
            region2: Second region

        Returns:
            bool: True if regions overlap
        """
        return self.coord_manager.check_region_overlap(region1, region2)

    def get_agent_coordinates(self, agent_id: str) -> Optional[Dict]:
        """Get coordinates for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary of coordinates or None if not found
        """
        return self.coord_manager.get_agent_coordinates(agent_id)

    def get_response_region(self, agent_id: str) -> Optional[Dict]:
        """Get response region for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Response region coordinates or None if not found
        """
        return self.coord_manager.get_response_region(agent_id)

    def _load_config(self, config_path):
        """Load coordinates from config file."""
        try:
            self.logger.debug("Loading coordinates from file")
            coords = load_coordinates(config_path)
            self.coord_manager = CoordinateManager(coords)
            self.logger.info(f"Loaded coordinates for {len(coords)} agents")
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.coord_manager = CoordinateManager({})

    def _save_coordinates(self, agent_id: str, coords: Dict) -> bool:
        """Save coordinates for an agent.

        Args:
            agent_id: ID of the agent
            coords: Coordinates to save

        Returns:
            bool: True if successful
        """
        try:
            save_coordinates(coords, self.config_path)
            self.coord_manager = CoordinateManager(load_coordinates(self.config_path))
            return True
        except Exception as e:
            self.logger.error(f"Error saving coordinates: {e}")
            return False

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        logger.debug("Setting up signal handlers")
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        logger.debug("Signal handlers set up")

    @contextmanager
    def _calibration_context(self):
        """Context manager for calibration process."""
        try:
            yield
        except Exception as e:
            logger.error(f"Error during calibration: {e}")
            self._cleanup_calibration()
        finally:
            self._cleanup_calibration()

    def _calibration_loop(self, agent_id: str):
        """Main calibration loop.

        Args:
            agent_id: ID of the agent being calibrated
        """
        try:
            while self.calibrating:
                if keyboard.is_pressed("esc"):
                    self.logger.info("Calibration cancelled by user")
                    break

                if keyboard.is_pressed("c"):
                    x, y = pyautogui.position()
                    self.points.append((x, y))
                    self.logger.debug(f"Captured point: ({x}, {y})")
                    time.sleep(0.5)  # Debounce

                time.sleep(0.1)  # Reduce CPU usage

        except Exception as e:
            self.logger.error(f"Error in calibration loop: {e}")
        finally:
            self._cleanup_calibration()

    def start_calibration(self, agent_id: str) -> bool:
        """Start calibration process for an agent.

        Args:
            agent_id: ID of the agent to calibrate

        Returns:
            bool: True if calibration started successfully
        """
        try:
            if self.calibrating:
                self.logger.warning("Calibration already in progress")
                return False

            self.calibrating = True
            self.current_step = 0
            self.points = []

            # Create and start calibration thread
            self.calibration_thread = threading.Thread(
                target=self._calibration_loop, args=(agent_id,), daemon=True
            )
            self.calibration_thread.start()

            return True
        except Exception as e:
            self.logger.error(f"Error starting calibration: {e}")
            self._cleanup_calibration()
            return False

    def _get_screenshot_logger(self, agent_id: str) -> ScreenshotLogger:
        """Get screenshot logger for agent.

        Args:
            agent_id: ID of the agent

        Returns:
            ScreenshotLogger instance
        """
        if agent_id not in self.screenshot_loggers:
            self.screenshot_loggers[agent_id] = ScreenshotLogger(agent_id)
        return self.screenshot_loggers[agent_id]

    def _validate_window_title(self, expected_title: str, timeout: float = 5.0) -> bool:
        """Validate window title.

        Args:
            expected_title: Expected window title
            timeout: Timeout in seconds

        Returns:
            bool: True if title matches
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                current_title = pyautogui.getActiveWindow().title
                if expected_title in current_title:
                    return True
                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)
        return False

    def _capture_debug_screenshot(self, agent_id: str, context: str) -> None:
        """Capture debug screenshot.

        Args:
            agent_id: ID of the agent
            context: Context for screenshot
        """
        try:
            logger = self._get_screenshot_logger(agent_id)
            logger.capture_screenshot(context)
        except Exception as e:
            self.logger.error(f"Error capturing debug screenshot: {e}")

    def _transform_coordinates(
        self,
        x: int,
        y: int,
        source_res: Tuple[int, int] = None,
        target_res: Tuple[int, int] = None,
    ) -> Tuple[int, int]:
        """Transform coordinates between resolutions.

        Args:
            x: X coordinate
            y: Y coordinate
            source_res: Source resolution
            target_res: Target resolution

        Returns:
            Tuple of transformed coordinates
        """
        if not source_res:
            source_res = (1920, 1080)  # Default source
        if not target_res:
            target_res = self._get_screen_resolution()

        scale_x = target_res[0] / source_res[0]
        scale_y = target_res[1] / source_res[1]

        return (int(x * scale_x), int(y * scale_y))

    def _transform_coordinate_dict(
        self,
        coords: Dict,
        source_res: Tuple[int, int] = None,
        target_res: Tuple[int, int] = None,
    ) -> Dict:
        """Transform coordinate dictionary between resolutions.

        Args:
            coords: Dictionary of coordinates
            source_res: Source resolution
            target_res: Target resolution

        Returns:
            Transformed coordinate dictionary
        """
        transformed = {}
        for key, coord in coords.items():
            transformed[key] = {
                "x": self._transform_coordinates(
                    coord["x"], coord["y"], source_res, target_res
                )[0],
                "y": self._transform_coordinates(
                    coord["x"], coord["y"], source_res, target_res
                )[1],
                "width": int(coord["width"] * (target_res[0] / source_res[0])),
                "height": int(coord["height"] * (target_res[1] / source_res[1])),
            }
        return transformed

    def _load_coordinates(self) -> Dict:
        """Load coordinates from file or use defaults.

        Returns:
            Dictionary of coordinates
        """
        try:
            if self.config_path and os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    coords = json.load(f)
                self.logger.debug(f"Loaded coordinates from {self.config_path}")
                return coords
            else:
                self.logger.warning(
                    f"Config file not found at {self.config_path}, using defaults"
                )
                return self._get_default_coordinates()
        except Exception as e:
            self.logger.error(f"Error loading coordinates: {e}")
            return self._get_default_coordinates()

    def _get_default_coordinates(self) -> Dict[str, Dict[str, int]]:
        """Get default coordinates based on screen resolution.

        Returns:
            Dictionary of default coordinates
        """
        try:
            width, height = pyautogui.size()

            # Calculate default positions
            center_x = width // 2
            center_y = height // 2

            # Define default regions
            return {
                "initial_spot": {"x": center_x, "y": center_y},
                "input_box": {"x": center_x, "y": height - 100},
                "copy_button": {"x": center_x + 100, "y": height - 100},
                "response_region": {
                    "x": center_x - 200,
                    "y": center_y - 200,
                    "width": 400,
                    "height": 400,
                },
            }
        except Exception as e:
            self.logger.error(f"Error getting default coordinates: {e}")
            return {}

    def _click_focus(self, x: int, y: int, max_attempts: int = 3) -> Tuple[int, int]:
        """Click to focus window at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            max_attempts: Maximum number of click attempts

        Returns:
            Tuple of final coordinates
        """
        for attempt in range(max_attempts):
            try:
                # Transform coordinates
                screen_x, screen_y = self._transform_coordinates(x, y)

                # Click to focus
                pyautogui.click(screen_x, screen_y)

                # Wait for focus
                time.sleep(FOCUS_ESTABLISH_DELAY)

                return screen_x, screen_y
            except Exception as e:
                self.logger.warning(f"Click focus attempt {attempt + 1} failed: {e}")
                if attempt == max_attempts - 1:
                    raise
                time.sleep(0.5)

        return x, y

    def send_message(self, agent_id: str, message: str) -> bool:
        """Send message to agent.

        Args:
            agent_id: ID of the agent
            message: Message to send

        Returns:
            bool: True if successful
        """
        try:
            # Get coordinates
            coords = self.get_agent_coordinates(agent_id)
            if not coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False

            # Click input box
            input_box = coords.get("input_box", {})
            if not input_box:
                self.logger.error("No input box coordinates found")
                return False

            x, y = input_box["x"], input_box["y"]
            screen_x, screen_y = self._click_focus(x, y)

            # Clear existing text
            self._clear_text()
            time.sleep(TEXT_CLEAR_DELAY)

            # Type message
            self._type_text(message)
            time.sleep(TYPING_COMPLETE_DELAY)

            # Send message
            pyautogui.press("enter")
            time.sleep(MESSAGE_SEND_DELAY)

            return True
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    def _load_onboarding_prompt(self, agent_id: str) -> str:
        """Load onboarding prompt for agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Onboarding prompt text
        """
        try:
            prompt_path = Path(f"prompts/{agent_id}_onboarding.txt")
            if prompt_path.exists():
                with open(prompt_path, "r") as f:
                    return f.read().strip()
            return ""
        except Exception as e:
            self.logger.error(f"Error loading onboarding prompt: {e}")
            return ""

    def perform_onboarding_sequence(
        self, agent_id: str, message: Optional[str] = None
    ) -> bool:
        """Perform onboarding sequence for agent.

        Args:
            agent_id: ID of the agent
            message: Optional custom message

        Returns:
            bool: True if successful
        """
        try:
            # Load prompt
            prompt = message or self._load_onboarding_prompt(agent_id)
            if not prompt:
                self.logger.error("No onboarding prompt available")
                return False

            # Split message if needed
            messages = self._split_message(prompt)

            # Send each message
            for msg in messages:
                if not self.send_message(agent_id, msg):
                    self.logger.error("Failed to send onboarding message")
                    return False
                time.sleep(MESSAGE_SEND_DELAY)

            return True
        except Exception as e:
            self.logger.error(f"Error during onboarding: {e}")
            return False

    def _split_message(self, message: str, max_length: int = 100) -> list:
        """Split message into smaller chunks.

        Args:
            message: Message to split
            max_length: Maximum length per chunk

        Returns:
            List of message chunks
        """
        if len(message) <= max_length:
            return [message]

        chunks = []
        current_chunk = ""

        for word in message.split():
            if len(current_chunk) + len(word) + 1 <= max_length:
                current_chunk += word + " "
            else:
                chunks.append(current_chunk.strip())
                current_chunk = word + " "

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def cleanup(self):
        """Clean up resources."""
        try:
            # Stop calibration if running
            if self.calibrating:
                self._cleanup_calibration()

            # Close screenshot loggers
            for logger in self.screenshot_loggers.values():
                logger.close()

            self.logger.debug("Cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    def move_to(self, x: int, y: int, duration: float = 0.5) -> Tuple[int, int]:
        """Move cursor to coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            duration: Movement duration

        Returns:
            Tuple of final coordinates
        """
        try:
            screen_x, screen_y = self._transform_coordinates(x, y)
            pyautogui.moveTo(screen_x, screen_y, duration=duration)
            return screen_x, screen_y
        except Exception as e:
            self.logger.error(f"Error moving cursor: {e}")
            return x, y

    def click(self, x: int, y: int, agent_id: Optional[str] = None) -> bool:
        """Click at coordinates.

        Args:
            x: X coordinate
            y: Y coordinate
            agent_id: Optional agent ID for logging

        Returns:
            bool: True if successful
        """
        try:
            screen_x, screen_y = self._transform_coordinates(x, y)
            pyautogui.click(screen_x, screen_y)

            if agent_id:
                self.logger.debug(
                    f"Clicked at ({screen_x}, {screen_y}) for agent {agent_id}"
                )
            return True
        except Exception as e:
            self.logger.error(f"Error clicking: {e}")
            return False

    def type_text(self, text: str, interval: float = 0.1) -> None:
        """Type text with interval between keystrokes.

        Args:
            text: Text to type
            interval: Interval between keystrokes
        """
        try:
            pyautogui.write(text, interval=interval)
        except Exception as e:
            self.logger.error(f"Error typing text: {e}")

    def press_key(self, key: str) -> None:
        """Press a key.

        Args:
            key: Key to press
        """
        try:
            pyautogui.press(key)
        except Exception as e:
            self.logger.error(f"Error pressing key: {e}")

    def hotkey(self, *keys: str) -> None:
        """Press a combination of keys.

        Args:
            *keys: Keys to press
        """
        try:
            pyautogui.hotkey(*keys)
        except Exception as e:
            self.logger.error(f"Error pressing hotkey: {e}")

    def screenshot(self, region: Optional[tuple] = None) -> Optional[Image.Image]:
        """Take a screenshot.

        Args:
            region: Optional region to capture

        Returns:
            Screenshot image or None if failed
        """
        try:
            return pyautogui.screenshot(region=region)
        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return None

    def _get_response(self, agent_id: str) -> Optional[str]:
        """Get response from agent's response region.

        Args:
            agent_id: ID of the agent

        Returns:
            Optional[str]: The captured response text, or None if capture failed
        """
        try:
            # Get coordinates for the agent
            coords = self.coords.get(agent_id)
            if not coords or "response_region" not in coords:
                self.logger.error(
                    f"No response region coordinates found for {agent_id}"
                )
                return None

            # Get response region coordinates
            region = coords["response_region"]
            if (
                not isinstance(region, dict)
                or "top_left" not in region
                or "bottom_right" not in region
            ):
                self.logger.error(f"Invalid response region format for {agent_id}")
                return None

            # Calculate region dimensions
            left = region["top_left"]["x"]
            top = region["top_left"]["y"]
            right = region["bottom_right"]["x"]
            bottom = region["bottom_right"]["y"]

            # Ensure valid region
            if not (left < right and top < bottom):
                self.logger.error(f"Invalid response region dimensions for {agent_id}")
                return None

            # Capture screenshot of response region
            region_width = right - left
            region_height = bottom - top
            screenshot = pyautogui.screenshot(
                region=(left, top, region_width, region_height)
            )

            # Convert screenshot to PIL Image if it's not already
            if not isinstance(screenshot, Image.Image):
                screenshot = Image.fromarray(screenshot)

            # Convert to grayscale for better OCR
            screenshot = screenshot.convert("L")

            # Use OCR to extract text
            try:
                text = pytesseract.image_to_string(screenshot)
                if text:
                    self.logger.debug(f"Captured response for {agent_id}: {text}")
                    return text.strip()
                else:
                    self.logger.warning(
                        f"No text found in response region for {agent_id}"
                    )
                    return None
            except Exception as e:
                self.logger.error(f"Error extracting text from response region: {e}")
                return None

        except Exception as e:
            self.logger.error(f"Error getting response for {agent_id}: {e}")
            return None

    def move_to_agent(self, agent_id: str) -> bool:
        """Move cursor to agent's initial position.

        Args:
            agent_id: ID of the agent

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.debug(f"Attempting to move to agent {agent_id}")
            self.logger.debug(f"Current coords state: {self.coords}")

            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False

            coords = self.coords[agent_id]
            self.logger.debug(f"Found coordinates for {agent_id}: {coords}")

            if "initial_spot" not in coords:
                self.logger.error(
                    f"No initial spot coordinates found for agent {agent_id}"
                )
                return False

            initial_spot = coords["initial_spot"]
            self.logger.debug(f"Initial spot coordinates: {initial_spot}")

            if not isinstance(initial_spot, dict):
                self.logger.error(f"Invalid initial spot format: {initial_spot}")
                return False

            if "x" not in initial_spot or "y" not in initial_spot:
                self.logger.error(f"Missing x or y in initial spot: {initial_spot}")
                return False

            # Use the transformed coordinates
            x = initial_spot["x"]
            y = initial_spot["y"]
            self.logger.debug(f"Moving to coordinates: ({x}, {y})")

            # Move to the coordinates
            self.move_to(x, y)
            return True
        except Exception as e:
            self.logger.error(f"Error moving to agent {agent_id}: {e}")
            return False

    def click_input_box(self, agent_id: str) -> bool:
        """Click the input box for the specified agent.

        Args:
            agent_id: ID of the agent

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False

            coords = self.coords[agent_id]
            if "input_box" not in coords:
                self.logger.error(
                    f"No input box coordinates found for agent {agent_id}"
                )
                return False

            x, y = coords["input_box"]["x"], coords["input_box"]["y"]
            self.click(x, y, agent_id)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking input box for agent {agent_id}: {e}")
            return False

    def click_copy_button(self, agent_id: str) -> bool:
        """Click the copy button for the specified agent.

        Args:
            agent_id: ID of the agent

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                self.logger.error(f"No coordinates found for agent {agent_id}")
                return False

            coords = self.coords[agent_id]
            if "copy_button" not in coords:
                self.logger.error(
                    f"No copy button coordinates found for agent {agent_id}"
                )
                return False

            x, y = coords["copy_button"]["x"], coords["copy_button"]["y"]
            self.click(x, y, agent_id)
            return True
        except Exception as e:
            self.logger.error(f"Error clicking copy button for agent {agent_id}: {e}")
            return False

    def _has_out_of_bounds_coordinates(self, coords: Dict) -> bool:
        """Check if any coordinates are outside screen bounds.

        Args:
            coords: Dictionary of coordinates to check

        Returns:
            bool: True if out of bounds found, False otherwise
        """
        try:
            for key, value in coords.items():
                if isinstance(value, dict) and "x" in value and "y" in value:
                    x, y = value["x"], value["y"]
                    if (
                        x < 0
                        or x > self.screen_width
                        or y < 0
                        or y > self.screen_height
                    ):
                        return True
            return False
        except Exception as e:
            self.logger.error(f"Error checking for out of bounds coordinates: {e}")
            return False
