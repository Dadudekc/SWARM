"""
UI Automation Module

Handles UI automation tasks using PyAutoGUI.
"""

import logging
import time
import json
import signal
from typing import Dict, Tuple, Optional
from pathlib import Path
import pyautogui
from PIL import Image

from ..cursor_controller import CursorController

# Configure logging
logger = logging.getLogger('agent_control.ui_automation')
logger.setLevel(logging.DEBUG)  # Set to DEBUG level

# Create console handler if none exists
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

class UIAutomation:
    """Handles UI automation for agent control."""
    
    def __init__(self):
        """Initialize UI automation."""
        logger.debug("Initializing UI automation")
        self.cursor = CursorController()
        self.coords = self._load_coordinates()
        self._setup_signal_handlers()
        logger.debug("UI automation initialized")
        
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        logger.debug("Setting up signal handlers")
        signal.signal(signal.SIGINT, self._handle_interrupt)
        signal.signal(signal.SIGTERM, self._handle_interrupt)
        logger.debug("Signal handlers set up")
        
    def _handle_interrupt(self, signum, frame):
        """Handle keyboard interrupt gracefully."""
        logger.info("Received interrupt signal, cleaning up...")
        self.cleanup()
        raise KeyboardInterrupt()
        
    def _load_coordinates(self) -> Dict:
        """Load cursor coordinates from JSON file."""
        logger.debug("Loading coordinates from file")
        try:
            config_path = Path("D:/SWARM/Dream.OS/runtime/config/cursor_agent_coords.json")
            
            if not config_path.exists():
                logger.error(f"Coordinates file not found at {config_path}")
                return self._get_default_coordinates()
                
            with open(config_path, 'r') as f:
                coords = json.load(f)
                
            # Convert nested coordinate dictionaries to tuples
            processed_coords = {}
            for agent_id, agent_coords in coords.items():
                if agent_id == "global_ui":
                    continue
                    
                processed_coords[agent_id] = {
                    "x": agent_coords["initial_spot"]["x"],
                    "y": agent_coords["initial_spot"]["y"],
                    "onboard_x": agent_coords["input_box"]["x"],
                    "onboard_y": agent_coords["input_box"]["y"],
                    "resume_x": agent_coords["copy_button"]["x"],
                    "resume_y": agent_coords["copy_button"]["y"],
                    "verify_x": agent_coords["input_box"]["x"],
                    "verify_y": agent_coords["input_box"]["y"],
                    "repair_x": agent_coords["input_box"]["x"],
                    "repair_y": agent_coords["input_box"]["y"],
                    "backup_x": agent_coords["input_box"]["x"],
                    "backup_y": agent_coords["input_box"]["y"],
                    "restore_x": agent_coords["input_box"]["x"],
                    "restore_y": agent_coords["input_box"]["y"],
                    "message_x": agent_coords["input_box"]["x"],
                    "message_y": agent_coords["input_box"]["y"]
                }
                
            logger.info(f"Loaded coordinates for {len(processed_coords)} agents")
            logger.debug(f"Processed coordinates: {processed_coords}")
            return processed_coords
            
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return self._get_default_coordinates()
            
    def _get_default_coordinates(self) -> Dict[str, Dict[str, int]]:
        """Get default coordinates for agents."""
        logger.debug("Using default coordinates")
        return {
            "Agent-1": {
                "x": 100,
                "y": 100,
                "onboard_x": 150,
                "onboard_y": 150,
                "resume_x": 200,
                "resume_y": 150,
                "verify_x": 250,
                "verify_y": 150,
                "repair_x": 300,
                "repair_y": 150,
                "backup_x": 350,
                "backup_y": 150,
                "restore_x": 400,
                "restore_y": 150,
                "message_x": 450,
                "message_y": 150
            },
            "Agent-2": {
                "x": 100,
                "y": 200,
                "onboard_x": 150,
                "onboard_y": 250,
                "resume_x": 200,
                "resume_y": 250,
                "verify_x": 250,
                "verify_y": 250,
                "repair_x": 300,
                "repair_y": 250,
                "backup_x": 350,
                "backup_y": 250,
                "restore_x": 400,
                "restore_y": 250,
                "message_x": 450,
                "message_y": 250
            }
        }
            
    def send_message(self, agent_id: str, message: str) -> bool:
        """Send a message using UI automation."""
        logger.debug(f"Sending message to {agent_id}: {message}")
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            coords = self.coords[agent_id]
            
            # Move to input box and click multiple times to ensure focus
            for i in range(3):
                logger.debug(f"Click attempt {i+1}/3")
                self.cursor.move_to(coords["message_x"], coords["message_y"])
                self.cursor.click()
                time.sleep(0.3)
            
            time.sleep(1.0)
            
            # Type the message
            logger.debug("Typing message")
            self.cursor.type_text(message)
            time.sleep(1.0)
            
            # Click input box again to ensure focus
            logger.debug("Clicking input box again")
            self.cursor.move_to(coords["message_x"], coords["message_y"])
            self.cursor.click()
            time.sleep(0.5)
            
            # Press Enter to send the message
            logger.debug("Pressing Enter to send")
            self.cursor.press_enter()
            time.sleep(1.0)
            
            logger.info(f"Message sent to {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {agent_id}: {e}")
            return False
            
    def _load_onboarding_prompt(self, agent_id: str) -> str:
        """Load the onboarding prompt from the agent's inbox."""
        logger.debug(f"Loading onboarding prompt for {agent_id}")
        try:
            inbox_path = Path(f"runtime/agent_memory/{agent_id}/inbox.json")
            if not inbox_path.exists():
                logger.warning(f"No inbox found for {agent_id}, using default prompt")
                return f"Welcome {agent_id}! Please confirm your initialization."
                
            with open(inbox_path, 'r') as f:
                inbox = json.load(f)
                
            if "onboarding_prompt" in inbox:
                logger.debug(f"Found onboarding prompt: {inbox['onboarding_prompt']}")
                return inbox["onboarding_prompt"]
            else:
                logger.warning(f"No onboarding prompt found in {agent_id}'s inbox")
                return f"Welcome {agent_id}! Please confirm your initialization."
                
        except Exception as e:
            logger.error(f"Error loading onboarding prompt: {e}")
            return f"Welcome {agent_id}! Please confirm your initialization."
            
    def perform_onboarding_sequence(self, agent_id: str, message: str = None) -> bool:
        """Perform the UI onboarding sequence."""
        logger.debug(f"Starting onboarding sequence for {agent_id}")
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False

            coords = self.coords[agent_id]
            logger.info(f"Starting UI onboarding sequence for {agent_id}")
            logger.debug(f"Using coordinates: {coords}")

            # Step 1: Click the agent's initial position
            logger.info("Step 1: Clicking agent position")
            logger.debug(f"Moving to coordinates: ({coords['x']}, {coords['y']})")
            self.cursor.move_to(coords["x"], coords["y"])
            time.sleep(0.2)
            logger.debug("Clicking at current position")
            self.cursor.click()
            time.sleep(0.5)
            logger.info("Step 1 completed")

            # Step 2: Activate chat interface (Ctrl+Enter)
            logger.info("Step 2: Activating chat interface")
            logger.debug("Pressing Ctrl+Enter")
            self.cursor.press_ctrl_enter()
            time.sleep(1.0)
            logger.info("Step 2 completed")

            # Step 3: Open fresh chat tab (Ctrl+N)
            logger.info("Step 3: Opening fresh chat tab")
            logger.debug("Pressing Ctrl+N")
            self.cursor.hotkey('ctrl', 'n')
            time.sleep(1.0)
            logger.info("Step 3 completed")

            # Step 4: Load and type onboarding prompt
            logger.info("Step 4: Loading onboarding prompt")
            prompt = message if message else self._load_onboarding_prompt(agent_id)
            logger.debug(f"Loaded prompt: {prompt}")
            logger.debug("Typing prompt")
            self.cursor.type_text(prompt)
            time.sleep(0.5)
            logger.info("Step 4 completed")

            # Step 5: Send the prompt
            logger.info("Step 5: Sending prompt")
            logger.debug("Pressing Enter to send")
            self.cursor.press_enter()
            time.sleep(1.0)
            logger.info("Step 5 completed")

            # Step 6: Start response monitoring
            logger.info("Step 6: Starting response monitoring")
            logger.debug("Response monitoring placeholder")
            logger.info("Step 6 completed")

            logger.info(f"Onboarding sequence completed for {agent_id}")
            return True
            
        except KeyboardInterrupt:
            logger.info("Onboarding sequence interrupted by user")
            self.cleanup()
            return False
        except Exception as e:
            logger.error(f"Error in onboarding sequence for {agent_id}: {e}")
            self.cleanup()
            return False
            
    def _split_message(self, message: str, max_length: int = 100) -> list:
        """Split a message into chunks of maximum length."""
        logger.debug(f"Splitting message into chunks of max length {max_length}")
        words = message.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_chunk.append(word)
                current_length += len(word) + 1
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        logger.debug(f"Split message into {len(chunks)} chunks")
        return chunks
        
    def get_agent_coordinates(self) -> Dict[str, Dict[str, int]]:
        """Get coordinates for all agents."""
        logger.debug("Getting agent coordinates")
        return self.coords
        
    def cleanup(self):
        """Clean up resources."""
        logger.debug("Cleaning up UI automation")
        try:
            # Reset PyAutoGUI settings
            pyautogui.PAUSE = 0.1
            logger.info("UI automation cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up UI automation: {e}")
            
    def move_to(self, x: int, y: int, duration: float = 0.5) -> None:
        """Move mouse to coordinates."""
        logger.debug(f"Moving mouse to ({x}, {y})")
        try:
            pyautogui.moveTo(x, y, duration=duration)
        except Exception as e:
            logger.error(f"Error moving mouse: {e}")
            
    def click(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """Click at coordinates or current position."""
        if x is not None and y is not None:
            logger.debug(f"Clicking at ({x}, {y})")
        else:
            logger.debug("Clicking at current position")
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y)
            else:
                pyautogui.click()
        except Exception as e:
            logger.error(f"Error clicking: {e}")
            
    def type_text(self, text: str, interval: float = 0.1) -> None:
        """Type text with specified interval."""
        logger.debug(f"Typing text: {text}")
        try:
            pyautogui.write(text, interval=interval)
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            
    def press_key(self, key: str) -> None:
        """Press a key."""
        logger.debug(f"Pressing key: {key}")
        try:
            pyautogui.press(key)
        except Exception as e:
            logger.error(f"Error pressing key: {e}")
            
    def hotkey(self, *keys: str) -> None:
        """Press a combination of keys."""
        logger.debug(f"Pressing hotkey: {' + '.join(keys)}")
        try:
            pyautogui.hotkey(*keys)
        except Exception as e:
            logger.error(f"Error pressing hotkey: {e}")
            
    def screenshot(self, region: Optional[tuple] = None) -> Optional[Image.Image]:
        """Take a screenshot."""
        logger.debug(f"Taking screenshot with region: {region}")
        try:
            return pyautogui.screenshot(region=region)
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None 