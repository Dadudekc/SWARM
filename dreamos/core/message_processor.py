"""
Message Processor

Processes queued messages and sends them to the UI using cursor control.
"""

import logging
import time
from typing import Optional
from .cell_phone import CellPhone, Message
from .cursor_controller import CursorController
import pyautogui
from agent_tools.agent_cellphone import send_message  # Fixed import path; was captainstools.agent_cellphone

logger = logging.getLogger('message_processor')

class MessageProcessor:
    """Processes queued messages and sends them to the UI."""
    
    def __init__(self):
        """Initialize the message processor."""
        self.cell_phone = CellPhone()
        self.cursor = CursorController()
        self.coords = self._load_coordinates()
        
    def _load_coordinates(self):
        """Load cursor coordinates from JSON file."""
        try:
            import json
            from pathlib import Path
            
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
            if msg['to_agent'] not in self.coords:
                logger.error(f"No coordinates found for {msg['to_agent']}")
                return
                
            coords = self.coords[msg['to_agent']]
            logger.info(f"Moving to input box at {coords['input_box']}")
            
            # Move to input box and double-click to ensure focus
            self.cursor.move_to(*coords["input_box"])
            self.cursor.click()
            time.sleep(0.5)
            self.cursor.click()  # Double click
            time.sleep(1.0)  # Longer delay to ensure focus
            
            # Type the message
            logger.info("Typing message...")
            self.cursor.type_text(msg['content'])
            time.sleep(2.0)  # Much longer delay to ensure message is fully typed
            
            # Double-click input box again to ensure focus
            self.cursor.move_to(*coords["input_box"])
            self.cursor.click()
            time.sleep(0.5)
            self.cursor.click()  # Double click
            time.sleep(1.0)
            
            # Press Enter to send the message
            logger.info("Pressing Enter to send message...")
            pyautogui.press('enter')  # Use press instead of hotkey
            time.sleep(2.0)  # Longer delay after sending
            
            # Move to copy button and click (for next message)
            logger.info(f"Moving to copy button at {coords['copy_button']}")
            self.cursor.move_to(*coords["copy_button"])
            self.cursor.click()
            time.sleep(1.0)  # Longer delay after clicking copy button
            
            logger.info(f"Message processed for {msg['to_agent']}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")

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