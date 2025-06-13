"""
Response Capture Module

Handles capturing and processing UI responses from Cursor.
"""

import logging
import time
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

from ..shared.coordinate_utils import load_coordinates
import pyautogui
from PIL import Image
import pytesseract
import numpy as np
import cv2

logger = logging.getLogger("agent_control.response_capture")


class ResponseCapture:
    """Handles capturing and processing UI responses."""

    def __init__(self, coords_path: str = "config/cursor_agent_coords.json"):
        """Initialize response capture.

        Args:
            coords_path: Path to coordinates config file
        """
        self.coords_path = Path(coords_path)
        self.coords = self._load_coordinates()

    def _load_coordinates(self) -> Dict:
        """Load coordinates from config file."""
        try:
            return load_coordinates(self.coords_path)
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return {}

    def capture_response(self, agent_id: str, timeout: int = 30) -> Optional[str]:
        """Capture response from agent's UI region.

        Args:
            agent_id: ID of the agent
            timeout: Maximum time to wait for response (seconds)

        Returns:
            Captured response text or None if timeout
        """
        if agent_id not in self.coords:
            logger.error(f"No coordinates found for {agent_id}")
            return None

        coords = self.coords[agent_id]
        region = coords.get("response_region")
        if not region:
            logger.error(f"No response region defined for {agent_id}")
            return None

        start_time = time.time()
        last_text = ""
        unchanged_count = 0

        while time.time() - start_time < timeout:
            try:
                # Calculate region dimensions
                x = region["top_left"]["x"]
                y = region["top_left"]["y"]
                width = region["bottom_right"]["x"] - x
                height = region["bottom_right"]["y"] - y

                # Log region details
                logger.debug(
                    f"[ResponseCapture] Capturing region: x={x}, y={y}, w={width}, h={height}"
                )

                # Validate region dimensions
                if width <= 0 or height <= 0:
                    logger.error(f"Invalid region dimensions: {width}x{height}")
                    return None

                # Get screen dimensions for validation
                screen_width, screen_height = pyautogui.size()
                if (
                    x < 0
                    or y < 0
                    or x + width > screen_width
                    or y + height > screen_height
                ):
                    logger.error(
                        f"Region is off-screen: x={x}, y={y}, w={width}, h={height}, screen={screen_width}x{screen_height}"
                    )
                    return None

                # Capture region
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                if not screenshot:
                    logger.error("Failed to capture screenshot")
                    return None

                # Convert PIL Image to numpy array
                img_array = np.array(screenshot)
                if img_array.size == 0:
                    logger.error(
                        "[ResponseCapture] Empty image array — region may be off-screen"
                    )
                    return None

                logger.debug(
                    f"[ResponseCapture] Captured image size: {img_array.shape}"
                )

                # Convert to grayscale for better OCR
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

                # Apply adaptive threshold to improve text detection
                thresh = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )

                # Convert back to PIL Image for pytesseract
                thresh_img = Image.fromarray(thresh)

                # OCR the image with improved config
                custom_config = r"--oem 3 --psm 6"
                text = pytesseract.image_to_string(thresh_img, config=custom_config)
                text = text.strip()

                if text:
                    if text == last_text:
                        unchanged_count += 1
                        if (
                            unchanged_count >= 3
                        ):  # Text unchanged for 3 consecutive checks
                            logger.info(f"Response captured for {agent_id}")
                            return text
                    else:
                        unchanged_count = 0
                        last_text = text

            except Exception as e:
                logger.error(f"Error capturing response: {e}")
                # Try direct OCR without preprocessing
                try:
                    if screenshot:
                        custom_config = r"--oem 3 --psm 6"
                        text = pytesseract.image_to_string(
                            screenshot, config=custom_config
                        )
                        text = text.strip()
                        if text:
                            if text == last_text:
                                unchanged_count += 1
                                if unchanged_count >= 3:
                                    logger.info(
                                        f"Response captured for {agent_id} (direct OCR)"
                                    )
                                    return text
                            else:
                                unchanged_count = 0
                                last_text = text
                except Exception as ocr_error:
                    logger.error(f"Error in direct OCR: {ocr_error}")

            time.sleep(0.5)  # Wait before next capture

        logger.warning(f"Timeout waiting for response from {agent_id}")
        return last_text if last_text else None

    def wait_for_copy_button(self, agent_id: str, timeout: int = 30) -> bool:
        """Wait for copy button to appear and click it.

        Args:
            agent_id: ID of the agent
            timeout: Maximum time to wait (seconds)

        Returns:
            True if button was clicked, False if timeout
        """
        if agent_id not in self.coords:
            logger.error(f"No coordinates found for {agent_id}")
            return False

        coords = self.coords[agent_id]
        copy_button = coords.get("copy_button")
        if not copy_button:
            logger.error(f"No copy button coordinates for {agent_id}")
            return False

        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check if copy button is visible
            try:
                button = pyautogui.locateOnScreen(
                    "assets/copy_button.png",
                    confidence=0.8,
                    region=(copy_button["x"] - 10, copy_button["y"] - 10, 20, 20),
                )
                if button:
                    pyautogui.click(copy_button["x"], copy_button["y"])
                    return True
            except Exception as e:
                logger.debug(f"Error checking copy button: {e}")

            time.sleep(0.5)

        logger.warning(f"Timeout waiting for copy button for {agent_id}")
        return False
