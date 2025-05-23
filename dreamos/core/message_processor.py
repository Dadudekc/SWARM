"""
Message Processor

Processes queued messages and sends them to the UI using cursor control.
"""

import logging
import time
from typing import Optional, Dict, List
from .cell_phone import CellPhone, Message
from .cursor_controller import CursorController
from .coordinate_manager import CoordinateManager
import pyautogui

logger = logging.getLogger('message_processor')

class MessageProcessor:
    """Processes queued messages and sends them to the UI."""
    
    def __init__(self):
        """Initialize the message processor."""
        self.cell_phone = CellPhone()
        self.cursor = CursorController()
        self.coordinate_manager = CoordinateManager()
        
    def process_queue(self):
        """Process all messages in the queue."""
        while True:
            # Get next message from queue
            msg = self.cell_phone.queue.dequeue()
            if not msg:
                logger.info("No messages in queue")
                break
                
            logger.info(f"Processing message to {msg['to_agent']}: {msg['content'][:50]}...")
            self._process_message(msg)
    
    def _process_message(self, msg: dict):
        """Process a single message by sending it to the UI."""
        try:
            coords = self.coordinate_manager.get_coordinates(msg['to_agent'])
            if not coords:
                logger.error(f"No coordinates found for {msg['to_agent']}")
                return
                
            # Get screen size
            screen_width, screen_height = pyautogui.size()
            
            # Ensure coordinates are within screen bounds
            input_box_x = max(0, min(coords['input_box'][0], screen_width - 1))
            input_box_y = max(0, min(coords['input_box'][1], screen_height - 1))
            copy_button_x = max(0, min(coords['copy_button'][0], screen_width - 1))
            copy_button_y = max(0, min(coords['copy_button'][1], screen_height - 1))
            
            logger.info(f"Moving to input box at ({input_box_x}, {input_box_y})")
            
            # Move to input box and double-click to ensure focus
            self.cursor.move_to(input_box_x, input_box_y)
            self.cursor.click()
            time.sleep(0.5)
            self.cursor.click()  # Double click
            time.sleep(1.0)  # Longer delay to ensure focus
            
            # Type the message
            logger.info("Typing message...")
            self.cursor.type_text(msg['content'])
            time.sleep(2.0)  # Much longer delay to ensure message is fully typed
            
            # Double-click input box again to ensure focus
            self.cursor.move_to(input_box_x, input_box_y)
            self.cursor.click()
            time.sleep(0.5)
            self.cursor.click()  # Double click
            time.sleep(1.0)
            
            # Press Enter to send the message
            logger.info("Pressing Enter to send message...")
            pyautogui.press('enter')  # Use press instead of hotkey
            time.sleep(2.0)  # Longer delay after sending
            
            # Move to copy button and click (for next message)
            logger.info(f"Moving to copy button at ({copy_button_x}, {copy_button_y})")
            self.cursor.move_to(copy_button_x, copy_button_y)
            self.cursor.click()
            time.sleep(1.0)  # Longer delay after clicking copy button
            
            logger.info(f"Message processed for {msg['to_agent']}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def send_message(self, agent_id: str, message: str, mode: str = "NORMAL") -> bool:
        """Send a message to a specific agent.
        
        Args:
            agent_id: The ID of the agent to send to
            message: The message content
            mode: The message mode (NORMAL, RESUME, etc.)
            
        Returns:
            True if message was sent successfully, False otherwise
        """
        try:
            if not self.coordinate_manager.get_coordinates(agent_id):
                logger.error(f"No coordinates found for agent {agent_id}")
                return False
                
            # Queue the message
            self.cell_phone.send_message(agent_id, message, mode)
            
            # Process the message immediately
            self._process_message({
                'to_agent': agent_id,
                'content': message
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    def send_to_all_agents(self, message: str, mode: str = "NORMAL") -> Dict[str, bool]:
        """Send a message to all agents.
        
        Args:
            message: The message content
            mode: The message mode
            
        Returns:
            Dictionary mapping agent IDs to success status
        """
        results = {}
        for agent_id in self.coordinate_manager.coordinates.keys():
            results[agent_id] = self.send_message(agent_id, message, mode)
        return results

def main():
    """Main entry point for processing messages."""
    processor = MessageProcessor()
    
    # Print initial queue status
    status = processor.cell_phone.get_status()
    print(f"\nInitial queue status:")
    print(f"Queue size: {status['queue_size']}")
    for msg in status['messages']:
        print(f"- To: {msg['to_agent']}, Status: {msg['status']}, Content: {msg['content'][:50]}...")
    
    # Process messages
    print("\nProcessing messages...")
    processor.process_queue()
    
    # Print final queue status
    status = processor.cell_phone.get_status()
    print(f"\nFinal queue status:")
    print(f"Queue size: {status['queue_size']}")
    for msg in status['messages']:
        print(f"- To: {msg['to_agent']}, Status: {msg['status']}, Content: {msg['content'][:50]}...")

if __name__ == "__main__":
    main() 