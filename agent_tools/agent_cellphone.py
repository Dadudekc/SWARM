"""
Agent Cellphone CLI

A command-line interface for Agent-1 to send messages to other agents.
Usage: python agent_cellphone.py --to AGENT --message "MESSAGE" [--priority PRIORITY] [--mode MODE]
      python agent_cellphone.py --welcome --to AGENT [--priority PRIORITY]
      python agent_cellphone.py --direct --to AGENT --message "MESSAGE" [--mode MODE]
"""

import argparse
import logging
import sys
import time
import pyautogui
from dreamos.core import CellPhone, MessageMode
from dreamos.core.coordinate_manager import CoordinateManager
from dreamos.core.agent_control.coordinate_transformer import CoordinateTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_cellphone')

# Configure stdout encoding for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_welcome_message() -> str:
    """Get the standard welcome message for new agents."""
    return """Welcome to Dream.OS! You are now part of our agent network. Your initial tasks:
1. Initialize your core systems
2. Establish communication channels
3. Begin monitoring your assigned domain
4. Report your status when ready

Let's begin your integration into the Dream.OS ecosystem."""

def direct_send_message(to_agent: str, message: str, mode: str = "NORMAL"):
    """Send a message directly using pyautogui automation.
    
    Args:
        to_agent: Target agent (e.g., "Agent-2")
        message: Message content
        mode: Message mode (NORMAL, PRIORITY, BULK, RESUME, SYNC, etc.)
    """
    try:
        # Initialize coordinate manager
        coord_manager = CoordinateManager()
        coords = coord_manager.get_coordinates(to_agent)
        
        if not coords:
            logger.error(f"No coordinates found for {to_agent}")
            print(f"[ERROR] No coordinates found for {to_agent}")
            return False
            
        # Helper function to get x,y from coordinate format
        def get_xy(coord):
            if isinstance(coord, tuple):
                return coord
            elif isinstance(coord, dict):
                return (coord['x'], coord['y'])
            return (0, 0)
        
        # Get coordinates in correct format
        input_box_coords = get_xy(coords['input_box'])
        copy_button_coords = get_xy(coords['copy_button'])
        
        logger.info(f"Moving to input box at {input_box_coords}")
        
        # Move to input box and double-click to ensure focus
        pyautogui.moveTo(input_box_coords[0], input_box_coords[1])
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.click()  # Double click
        time.sleep(1.0)  # Longer delay to ensure focus
        
        # Type the message
        logger.info("Typing message...")
        pyautogui.write(message)
        time.sleep(2.0)  # Much longer delay to ensure message is fully typed
        
        # Double-click input box again to ensure focus
        pyautogui.moveTo(input_box_coords[0], input_box_coords[1])
        pyautogui.click()
        time.sleep(0.5)
        pyautogui.click()  # Double click
        time.sleep(1.0)
        
        # Press Enter to send the message
        logger.info("Pressing Enter to send message...")
        pyautogui.press('enter')
        time.sleep(2.0)  # Longer delay after sending
        
        # Move to copy button and click (for next message)
        logger.info(f"Moving to copy button at {copy_button_coords}")
        pyautogui.moveTo(copy_button_coords[0], copy_button_coords[1])
        pyautogui.click()
        time.sleep(1.0)  # Longer delay after clicking copy button
        
        logger.info(f"Message sent successfully to {to_agent}")
        print(f"[OK] Message sent to {to_agent}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        print(f"Error: {e}")
        return False

def send_message(to_agent: str, message: str, priority: int = 0, mode: str = "NORMAL"):
    """Send a message to another agent.
    
    Args:
        to_agent: Target agent (e.g., "Agent-2")
        message: Message content
        priority: Message priority (0-5)
        mode: Message mode (NORMAL, PRIORITY, BULK, RESUME, SYNC, etc.)
    """
    try:
        # Initialize cell phone
        phone = CellPhone()
        logger.info("Cell phone initialized")
        
        # Send message
        success = phone.send_message(
            to_agent=to_agent,
            content=message,
            mode=mode,
            priority=priority
        )
        
        if success:
            logger.info(f"Message sent successfully to {to_agent}")
            print(f"[OK] Message sent to {to_agent}")
            
            # Get status
            status = phone.get_message_status(to_agent)
            logger.info(f"Cell phone status: {status}")
            print(f"Status: {status}")
        else:
            logger.error(f"Failed to send message to {to_agent}")
            print(f"[ERROR] Failed to send message to {to_agent}")
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        print(f"Error: {e}")
    finally:
        logger.info("Message sending completed")

def main():
    """Parse command line arguments and send message."""
    parser = argparse.ArgumentParser(description="Send messages to other agents")
    
    # Welcome message flag
    parser.add_argument("--welcome", action="store_true", 
                      help="Send the standard welcome message")
    
    # Direct send flag
    parser.add_argument("--direct", action="store_true",
                      help="Send message directly using pyautogui (bypass queue)")
    
    # Required arguments (if not using welcome message)
    parser.add_argument("--to", required=True, help="Target agent (e.g., Agent-2)")
    parser.add_argument("--message", required=False, help="Message content")
    
    # Optional arguments
    parser.add_argument("--priority", type=int, default=0, 
                      help="Message priority (0-5, higher is more urgent)")
    parser.add_argument("--mode", default="NORMAL",
                      choices=[mode.name for mode in MessageMode],
                      help="Message mode (NORMAL, PRIORITY, BULK, RESUME, SYNC, etc.)")
    
    args = parser.parse_args()
    
    # Validate priority
    if not 0 <= args.priority <= 5:
        logger.error("Priority must be between 0 and 5")
        print("Error: Priority must be between 0 and 5")
        return
    
    # Get message content
    if args.welcome:
        message = get_welcome_message()
        mode = "RESUME"  # Use RESUME mode for welcome messages
    else:
        if not args.message:
            logger.error("Message content is required when not using --welcome")
            print("Error: Message content is required when not using --welcome")
            return
        message = args.message
        mode = args.mode
    
    # Send message
    if args.direct:
        direct_send_message(args.to, message, mode)
    else:
        send_message(args.to, message, args.priority, mode)

if __name__ == "__main__":
    main() 