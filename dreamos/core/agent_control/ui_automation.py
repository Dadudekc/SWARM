"""
UI Automation Module


Handle channel test. Please respond if you receive this message.CoCmommumnuinciactaitoino n chcahnannenle lte sttes.t .PCommunications all cursor and UI interaction functionality for agent control.
"""

import logging
import time
from typing import Dict, Tuple, Optional
from pathlib import Path
import json

from ..cursor_controller import CursorController

logger = logging.getLogger('agent_control.ui_automation')

class UIAutomation:
    """Handles UI automation for agent control."""
    
    def __init__(self):
        """Initialize UI automation."""
        self.cursor = CursorController()
        self.coords = self._load_coordinates()
        
    def _load_coordinates(self) -> Dict:
        """Load cursor coordinates from JSON file."""
        try:
            config_path = Path("D:/SWARM/Dream.OS/runtime/config/cursor_agent_coords.json")
            
            if not config_path.exists():
                logger.error(f"Coordinates file not found at {config_path}")
                return {}
                
            with open(config_path, 'r') as f:
                coords = json.load(f)
                
            # Convert nested coordinate dictionaries to tuples
            processed_coords = {}
            for agent_id, agent_coords in coords.items():
                if agent_id == "global_ui":
                    continue
                    
                processed_coords[agent_id] = {
                    "input_box": (agent_coords["input_box"]["x"], agent_coords["input_box"]["y"]),
                    "initial_spot": (agent_coords["initial_spot"]["x"], agent_coords["initial_spot"]["y"]),
                    "copy_button": (agent_coords["copy_button"]["x"], agent_coords["copy_button"]["y"])
                }
                
            logger.info(f"Loaded coordinates for {len(processed_coords)} agents")
            return processed_coords
            
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return {}
            
    def send_message(self, agent_id: str, message: str) -> bool:
        """Send a message using UI automation.
        
        Args:
            agent_id: The agent ID to send to
            message: The message to send
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            coords = self.coords[agent_id]
            
            # Move to input box and click multiple times to ensure focus
            for _ in range(3):
                self.cursor.move_to(*coords["input_box"])
                self.cursor.click()
                time.sleep(0.3)
            
            time.sleep(1.0)
            
            # Type the message
            logger.info("Typing message...")
            self.cursor.type_text(message)
            time.sleep(1.0)
            
            # Click input box again to ensure focus
            self.cursor.move_to(*coords["input_box"])
            self.cursor.click()
            time.sleep(0.5)
            
            # Press Enter to send the message
            logger.info("Pressing Enter to send message...")
            self.cursor.press_enter()
            time.sleep(1.0)
            
            # Move to copy button and click (for next message)
            logger.info(f"Moving to copy button at {coords['copy_button']}")
            self.cursor.move_to(*coords["copy_button"])
            self.cursor.click()
            
            logger.info(f"Message sent to {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to {agent_id}: {e}")
            return False
            
    def perform_onboarding_sequence(self, agent_id: str, message: str) -> bool:
        """Perform the UI onboarding sequence.
        
        Args:
            agent_id: The agent ID to onboard
            message: The onboarding message
            
        Returns:
            bool: True if sequence was successful
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False

            coords = self.coords[agent_id]
            logger.info(f"Starting UI onboarding sequence for {agent_id}")

            # UI automation sequence
            self.cursor.move_to(*coords["initial_spot"])
            time.sleep(0.2)
            self.cursor.click()
            time.sleep(0.2)
            self.cursor.press_ctrl_enter()
            time.sleep(0.3)
            self.cursor.press_ctrl_n()
            time.sleep(0.3)

            # Send message chunks
            chunks = self._split_message(message)
            for i, chunk in enumerate(chunks, 1):
                self.cursor.type_text(chunk)
                time.sleep(0.2)
                if i < len(chunks):
                    self.cursor.press_enter()
                    time.sleep(0.3)

            self.cursor.press_enter()
            time.sleep(0.2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in onboarding sequence for {agent_id}: {e}")
            return False
            
    def _split_message(self, message: str, max_length: int = 100) -> list:
        """Split a message into chunks of maximum length."""
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
        
        return chunks 