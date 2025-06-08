"""
Test suite for Agent-1 tasks:
1. Window focus verification
2. Screenshot quality validation
"""

import pytest
import pyautogui
from pathlib import Path
from dreamos.core.agent_control.agent_control import AgentControl
import os
import sys
import types
import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestAgent1Tasks:
    @pytest.fixture
    def agent_control(self, tmp_path):
        """Initialize AgentControl for testing."""
        config_path = tmp_path / "test_config.json"
        config = {
            "Agent-1": {
                "initial_spot": {"x": 100, "y": 200},
                "input_box": {"x": 150, "y": 250},
                "copy_button": {"x": 200, "y": 300},
                "response_region": {
                    "top_left": {"x": 400, "y": 400},
                    "bottom_right": {"x": 600, "y": 600}
                }
            }
        }
        config_path.write_text(json.dumps(config))
        return AgentControl(config_path=str(config_path))
    
    def is_headless_or_mocked(self):
        """Check if running in a headless environment or pyautogui is mocked."""
        try:
            # Check if running in a headless environment
            if os.environ.get("DISPLAY", "") == "" and sys.platform != "win32":
                logger.info("Running in headless environment (no display)")
                return True
                
            # Check if pyautogui is mocked
            if isinstance(pyautogui.moveTo, types.FunctionType) and "MagicMock" in str(type(pyautogui.screenshot)):
                logger.info("PyAutoGUI is mocked")
                return True
                
            # Try a basic GUI op
            width, height = pyautogui.size()
            logger.info(f"Screen size detected: {width}x{height}")
            if width == 0 or height == 0:
                logger.info("Invalid screen dimensions detected")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error checking GUI environment: {e}")
            return True

    def test_window_focus_verification(self, agent_control):
        """Test window focus verification for Agent-1."""
        if self.is_headless_or_mocked():
            pytest.skip("Skipping GUI test: pyautogui not available or running headless/mocked.")
            
        logger.info("Starting window focus verification test")
        
        try:
            # Move to agent position
            logger.info("Moving to agent position")
            assert agent_control.move_to_agent("Agent-1"), "Failed to move to Agent-1 position"
            
            # Click input box to verify focus
            logger.info("Clicking input box")
            assert agent_control.click_input_box("Agent-1"), "Failed to click input box"
            
            # Verify window is in focus
            logger.info("Checking window focus")
            active_window = pyautogui.getActiveWindow()
            assert active_window is not None, "No active window detected"
            logger.info(f"Active window title: {active_window.title}")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise
        
    def test_screenshot_quality(self, agent_control):
        """Test screenshot quality for Agent-1."""
        if self.is_headless_or_mocked():
            pytest.skip("Skipping GUI test: pyautogui not available or running headless/mocked.")
            
        logger.info("Starting screenshot quality test")
        
        try:
            # Get response region
            logger.info("Getting response region")
            response_region = agent_control.get_response_region("Agent-1")
            assert response_region is not None, "Failed to get response region"
            
            # Take screenshot of response region
            logger.info("Taking screenshot")
            screenshot = pyautogui.screenshot(region=(
                response_region["top_left"]["x"],
                response_region["top_left"]["y"],
                response_region["bottom_right"]["x"] - response_region["top_left"]["x"],
                response_region["bottom_right"]["y"] - response_region["top_left"]["y"]
            ))
            
            # Basic quality checks
            logger.info(f"Screenshot dimensions: {screenshot.width}x{screenshot.height}")
            assert screenshot.width > 0, "Screenshot width is 0"
            assert screenshot.height > 0, "Screenshot height is 0"
            
            # Check if screenshot is not completely black or white
            pixels = screenshot.getdata()
            unique_colors = len(set(pixels))
            logger.info(f"Number of unique colors: {unique_colors}")
            assert unique_colors > 2, "Screenshot appears to be blank or solid color"
            
            # Save screenshot for manual verification
            screenshot_path = Path("test_logs/agent1_screenshot.png")
            screenshot_path.parent.mkdir(exist_ok=True)
            screenshot.save(screenshot_path)
            logger.info(f"Screenshot saved to {screenshot_path}")
            
        except Exception as e:
            logger.error(f"Test failed: {e}")
            raise 
