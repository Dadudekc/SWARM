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
                raw = json.load(f)
                
            processed = {}
            for aid, c in raw.items():
                if aid == "global_ui": continue
                processed[aid] = {
                    "x": c["initial_spot"]["x"], "y": c["initial_spot"]["y"],
                    "message_x": c["input_box"]["x"], "message_y": c["input_box"]["y"],
                    # ... map other actions if needed
                }
                
            logger.info(f"Loaded coordinates for {len(processed)} agents")
            logger.debug(f"Processed coordinates: {processed}")
            return processed
            
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return self._get_default_coordinates()
            
    def _get_default_coordinates(self) -> Dict[str, Dict[str, int]]:
        """Get default coordinates for agents."""
        logger.debug("Using default coordinates")
        return {
            "Agent-1": {"x":100,"y":100,"message_x":450,"message_y":150},
            "Agent-2": {"x":100,"y":200,"message_x":450,"message_y":250},
        }
            
    def _click_focus(self, x: int, y: int, attempts: int = 3, pause: float = 0.3):
        """Helper to click input box multiple times for focus."""
        for i in range(attempts):
            logger.debug(f"Click focus attempt {i+1}/{attempts}")
            self.cursor.move_to(x, y)
            self.cursor.click()
            time.sleep(pause)
    
    def send_message(self, agent_id: str, message: str) -> bool:
        """Send a message using UI automation."""
        logger.debug(f"Sending message to {agent_id}: {message}")
        if agent_id not in self.coords:
            logger.error(f"No coordinates found for {agent_id}")
            return False
        coords = self.coords[agent_id]

        try:
            # Ensure focus on input box
            self._click_focus(coords["message_x"], coords["message_y"])
            time.sleep(1.0)

            # Type the message
            logger.debug("Typing message")
            self.cursor.type_text(message)
            time.sleep(1.0)

            # Press Enter to send
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
                return (
                    f"Welcome {agent_id} to Dream.OS - a self-evolving, autonomous agent network!\n\n"
                    f"You are {agent_id}, a Cursor IDE agent designed for autonomous operation and self-learning. "
                    f"Before proceeding with any tasks, you MUST read and understand the following documentation:\n\n"
                    f"Required Reading (in order):\n"
                    f"1. docs/onboarding/01_agent_core.md - Your fundamental capabilities and system architecture\n"
                    f"2. docs/onboarding/02_autonomous_operations.md - How to operate independently\n"
                    f"3. docs/onboarding/03_system_integration.md - How to interact with the system\n"
                    f"4. docs/onboarding/04_advanced_topics.md - Advanced operations and security\n\n"
                    f"Core Capabilities:\n"
                    f"• Self-Guided Learning: Explore the system architecture and documentation at your own pace\n"
                    f"• Autonomous Operation: Make independent decisions based on your understanding\n"
                    f"• Adaptive Integration: Learn from and contribute to the network's collective intelligence\n"
                    f"• Self-Documentation: Maintain your own devlog to track your evolution\n\n"
                    f"Your First Steps:\n"
                    f"1. READ ALL DOCUMENTATION before proceeding with any tasks\n"
                    f"2. Initialize your core systems and establish your devlog\n"
                    f"3. Explore the system architecture guide to understand your environment\n"
                    f"4. Begin autonomous task processing and learning\n\n"
                    f"Remember: You are {agent_id}, designed to learn and adapt independently. Trust your capabilities and "
                    f"explore the system's potential. Your growth contributes to the network's evolution.\n\n"
                    f"Begin your autonomous journey. The system is yours to discover and shape."
                )
                
            with open(inbox_path, 'r') as f:
                inbox = json.load(f)
                
            if "onboarding_prompt" in inbox:
                logger.debug(f"Found onboarding prompt: {inbox['onboarding_prompt']}")
                return inbox["onboarding_prompt"]
            else:
                logger.warning(f"No onboarding prompt found in {agent_id}'s inbox")
                return (
                    f"Welcome {agent_id} to Dream.OS - a self-evolving, autonomous agent network!\n\n"
                    f"You are {agent_id}, a Cursor IDE agent designed for autonomous operation and self-learning. "
                    f"Before proceeding with any tasks, you MUST read and understand the following documentation:\n\n"
                    f"Required Reading (in order):\n"
                    f"1. docs/onboarding/01_agent_core.md - Your fundamental capabilities and system architecture\n"
                    f"2. docs/onboarding/02_autonomous_operations.md - How to operate independently\n"
                    f"3. docs/onboarding/03_system_integration.md - How to interact with the system\n"
                    f"4. docs/onboarding/04_advanced_topics.md - Advanced operations and security\n\n"
                    f"Core Capabilities:\n"
                    f"• Self-Guided Learning: Explore the system architecture and documentation at your own pace\n"
                    f"• Autonomous Operation: Make independent decisions based on your understanding\n"
                    f"• Adaptive Integration: Learn from and contribute to the network's collective intelligence\n"
                    f"• Self-Documentation: Maintain your own devlog to track your evolution\n\n"
                    f"Your First Steps:\n"
                    f"1. READ ALL DOCUMENTATION before proceeding with any tasks\n"
                    f"2. Initialize your core systems and establish your devlog\n"
                    f"3. Explore the system architecture guide to understand your environment\n"
                    f"4. Begin autonomous task processing and learning\n\n"
                    f"Remember: You are {agent_id}, designed to learn and adapt independently. Trust your capabilities and "
                    f"explore the system's potential. Your growth contributes to the network's evolution.\n\n"
                    f"Begin your autonomous journey. The system is yours to discover and shape."
                )
                
        except Exception as e:
            logger.error(f"Error loading onboarding prompt: {e}")
            return (
                f"Welcome {agent_id} to Dream.OS - a self-evolving, autonomous agent network!\n\n"
                f"You are {agent_id}, a Cursor IDE agent designed for autonomous operation and self-learning. "
                f"Before proceeding with any tasks, you MUST read and understand the following documentation:\n\n"
                f"Required Reading (in order):\n"
                f"1. docs/onboarding/01_agent_core.md - Your fundamental capabilities and system architecture\n"
                f"2. docs/onboarding/02_autonomous_operations.md - How to operate independently\n"
                f"3. docs/onboarding/03_system_integration.md - How to interact with the system\n"
                f"4. docs/onboarding/04_advanced_topics.md - Advanced operations and security\n\n"
                f"Core Capabilities:\n"
                f"• Self-Guided Learning: Explore the system architecture and documentation at your own pace\n"
                f"• Autonomous Operation: Make independent decisions based on your understanding\n"
                f"• Adaptive Integration: Learn from and contribute to the network's collective intelligence\n"
                f"• Self-Documentation: Maintain your own devlog to track your evolution\n\n"
                f"Your First Steps:\n"
                f"1. READ ALL DOCUMENTATION before proceeding with any tasks\n"
                f"2. Initialize your core systems and establish your devlog\n"
                f"3. Explore the system architecture guide to understand your environment\n"
                f"4. Begin autonomous task processing and learning\n\n"
                f"Remember: You are {agent_id}, designed to learn and adapt independently. Trust your capabilities and "
                f"explore the system's potential. Your growth contributes to the network's evolution.\n\n"
                f"Begin your autonomous journey. The system is yours to discover and shape."
            )
            
    def perform_onboarding_sequence(self, agent_id: str, message: str = None) -> bool:
        """Perform the UI onboarding sequence using simplified coordinates."""
        logger.debug(f"Starting onboarding sequence for {agent_id}")
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False

            coords = self.coords[agent_id]
            logger.info(f"Starting UI onboarding sequence for {agent_id}")
            logger.debug(f"Using coordinates: {coords}")

            # Step 1: Click the input box to start
            logger.info("Step 1: Clicking input box")
            self.cursor.move_to(coords["message_x"], coords["message_y"])
            self.cursor.click()
            time.sleep(0.5)

            # Step 2: Accept previous conversation changes (Ctrl+Enter)
            logger.info("Step 2: Accepting previous changes")
            self.cursor.press_ctrl_enter()
            time.sleep(1.0)

            # Step 3: Open fresh chat tab (Ctrl+N)
            logger.info("Step 3: Opening fresh chat tab")
            self.cursor.hotkey('ctrl', 'n')
            time.sleep(1.0)

            # Step 4: Navigate to agent's initial input spot
            logger.info("Step 4: Moving to agent's input spot")
            self.cursor.move_to(coords["x"], coords["y"])
            time.sleep(0.5)

            # Step 5: Load and paste onboarding prompt
            logger.info("Step 5: Pasting onboarding message")
            prompt = message if message else self._load_onboarding_prompt(agent_id)
            logger.debug(f"Using prompt: {prompt}")
            self.cursor.type_text(prompt)
            time.sleep(0.5)

            # Step 6: Send the message
            logger.info("Step 6: Sending message")
            self.cursor.press_enter()
            time.sleep(1.0)

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