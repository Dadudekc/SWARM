"""
Agent Captain

Provides programmatic interface for captain agents to manage and onboard other agents.
"""

import logging
import time
from typing import List, Optional
from pathlib import Path
import json
import shutil
import os

from .cell_phone import CellPhone, Message
from .cursor_controller import CursorController
from .agent_resume_main import MessageMode
from agent_tools.agent_cellphone import send_message
from agent_tools.utils.init_mailbox import AgentMailbox

logger = logging.getLogger('agent_captain')

class AgentCaptain:
    """Captain agent interface for managing and onboarding other agents."""
    
    def __init__(self):
        """Initialize the captain agent interface."""
        self.cell_phone = CellPhone()
        self.cursor = CursorController()
        self.coords = self._load_coordinates()
        
    def _load_coordinates(self):
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
    
    def onboard_agent(self, agent_id: str, message: Optional[str] = None) -> bool:
        """Onboard a single agent using the full onboarding sequence.
        
        Args:
            agent_id: The ID of the agent to onboard (e.g. "Agent-1")
            message: Optional custom onboarding message. If None, uses default.
            
        Returns:
            bool: True if onboarding was successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            # Default onboarding message if none provided
            if not message:
                message = """Welcome to Dream.OS! You are now part of our agent network.
                
Your initial tasks:
1. Initialize your core systems
2. Establish communication channels
3. Begin monitoring your assigned domain
4. Report your status when ready

Let's begin your integration into the Dream.OS ecosystem."""

            coords = self.coords[agent_id]
            logger.info(f"Starting onboarding sequence for {agent_id}")

            # 1. Go to initial spot
            logger.debug(f"Moving to initial position for {agent_id}")
            self.cursor.move_to(*coords["initial_spot"])
            time.sleep(0.2)

            # 2. Click
            logger.debug("Clicking at position")
            self.cursor.click()
            time.sleep(0.2)

            # 3. Press Ctrl+Enter
            logger.debug("Pressing Ctrl+Enter")
            self.cursor.press_ctrl_enter()
            time.sleep(0.3)

            # 4. Press Ctrl+N
            logger.debug("Pressing Ctrl+N")
            self.cursor.press_ctrl_n()
            time.sleep(0.3)

            # 5. Send message chunks
            logger.debug("Sending message chunks")
            chunks = self._split_message(message)
            for i, chunk in enumerate(chunks, 1):
                logger.debug(f"Sending chunk {i}/{len(chunks)}")
                self.cursor.type_text(chunk)
                time.sleep(0.2)
                if i < len(chunks):
                    self.cursor.press_enter()
                    time.sleep(0.3)

            # 6. Press Enter for final chunk
            logger.debug("Pressing Enter for final chunk")
            self.cursor.press_enter()
            time.sleep(0.2)

            logger.info(f"Onboarding sequence completed for {agent_id}")

            # Also send via cell phone as backup
            logger.debug("Sending backup message via cell phone")
            self.send_message(agent_id, message, MessageMode.NORMAL)
            
            return True

        except Exception as e:
            logger.error(f"Error in onboarding sequence for {agent_id}: {e}")
            # Try to send via cell phone as fallback
            try:
                logger.info("Attempting fallback to cell phone only")
                self.send_message(agent_id, message, MessageMode.NORMAL)
                return True
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                return False
    
    def onboard_agents(self, agent_ids: List[str], message: Optional[str] = None) -> dict:
        """Onboard multiple agents.
        
        Args:
            agent_ids: List of agent IDs to onboard
            message: Optional custom onboarding message
            
        Returns:
            dict: Results for each agent, e.g. {"Agent-1": True, "Agent-2": False}
        """
        results = {}
        for agent_id in agent_ids:
            success = self.onboard_agent(agent_id, message)
            results[agent_id] = success
        return results
    
    def send_message(self, agent_id: str, message: str, mode: MessageMode = MessageMode.NORMAL) -> bool:
        """Send a message to an agent.
        
        Args:
            agent_id: The ID of the agent to send to
            message: The message to send
            mode: The message mode (NORMAL, RESUME, etc.)
            
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
    
    def _split_message(self, message: str, max_length: int = 100) -> List[str]:
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
    
    def get_agent_status(self, agent_id: str) -> dict:
        """Get the current status of an agent.
        
        Args:
            agent_id: The ID of the agent to check
            
        Returns:
            dict: Status information about the agent
        """
        try:
            # Send a status check message
            message = "[STATUS] Please report your current status."
            success = self.send_message(agent_id, message, MessageMode.VERIFY)
            
            return {
                "agent_id": agent_id,
                "coordinates_available": agent_id in self.coords,
                "last_message_sent": success,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error getting status for {agent_id}: {e}")
            return {
                "agent_id": agent_id,
                "error": str(e),
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_all_agent_statuses(self) -> dict:
        """Get status for all available agents.
        
        Returns:
            dict: Status information for all agents
        """
        return {
            agent_id: self.get_agent_status(agent_id)
            for agent_id in self.coords.keys()
        }

    def clear_agent_messages(self, agent_id: str) -> bool:
        """Clear all messages for a specific agent.
        
        Args:
            agent_id: The ID of the agent whose messages should be cleared
            
        Returns:
            bool: True if messages were cleared successfully
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            # Clear messages in cell phone
            self.cell_phone.clear_messages(agent_id)
            
            # Move to input box and clear it
            coords = self.coords[agent_id]
            self.cursor.move_to(*coords["input_box"])
            self.cursor.click()
            time.sleep(0.2)
            
            # Select all and delete
            self.cursor.press_ctrl_a()
            time.sleep(0.2)
            self.cursor.press_delete()
            time.sleep(0.2)
            
            logger.info(f"Cleared messages for {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing messages for {agent_id}: {e}")
            return False

def move_to_captainstools(source_path: str, target_dir: str = "captainstools") -> bool:
    """Move a file to the captainstools subdirectory.
    
    Args:
        source_path: The path of the file to move.
        target_dir: The target subdirectory (default: 'captainstools').
        
    Returns:
        bool: True if the file was moved successfully, False otherwise.
    """
    try:
        # Create the target directory if it doesn't exist
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
        
        # Get the filename from the source path
        filename = os.path.basename(source_path)
        
        # Define the target path
        target_path = os.path.join(target_dir, filename)
        
        # Move the file
        shutil.move(source_path, target_path)
        
        logger.info(f"File moved successfully: {source_path} -> {target_path}")
        return True
    except Exception as e:
        logger.error(f"Error moving file: {e}")
        return False

def main():
    """Example usage of the AgentCaptain class."""
    captain = AgentCaptain()
    
    # Example: Onboard Agent-1
    success = captain.onboard_agent("Agent-1")
    print(f"Onboarding Agent-1: {'Success' if success else 'Failed'}")
    
    # Example: Get status of all agents
    statuses = captain.get_all_agent_statuses()
    print("\nAgent Statuses:")
    for agent_id, status in statuses.items():
        print(f"{agent_id}: {status}")

if __name__ == "__main__":
    main() 