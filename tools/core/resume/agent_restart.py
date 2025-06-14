"""
Agent Restart System

Restarts agents using Ctrl+N and sends initial messages to their input boxes.
Ensures agents know where to respond in the message area.
"""

import time
import logging
import pyautogui
import json
from pathlib import Path
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('agent_restart')

def load_coordinates():
    """Load agent coordinates from config file."""
    coords_file = Path("runtime/config/cursor_agent_coords.json")
    with open(coords_file, 'r') as f:
        return json.load(f)

def restart_agent(agent_name: str):
    """Restart an agent using Ctrl+N."""
    try:
        coords = load_coordinates()
        agent_coords = coords[agent_name]
        
        # Move to agent window and press Ctrl+N
        window_pos = agent_coords['initial_spot']
        pyautogui.moveTo(window_pos['x'], window_pos['y'])
        pyautogui.click()
        time.sleep(1)  # Wait for window focus
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(2)  # Wait for restart
        
        logger.info(f"Restarted {agent_name}")
        return True
    except Exception as e:
        logger.error(f"Error restarting {agent_name}: {e}")
        return False

def send_initial_message(agent_name: str):
    """Send initial message to agent's input box."""
    try:
        coords = load_coordinates()
        agent_coords = coords[agent_name]
        
        # Move to input box
        input_box = agent_coords['input_box_initial']  # Use initial input box
        pyautogui.moveTo(input_box['x'], input_box['y'])
        pyautogui.click()
        time.sleep(0.5)
        
        # Type message
        message = f"Agent {agent_name}, this is your initial message. Please respond in the message area. Your sequence position is: "
        if agent_name == "Agent-1":
            message += "1st"
        elif agent_name == "Agent-2":
            message += "2nd"
        elif agent_name == "Agent-4":
            message += "3rd"
        elif agent_name == "Agent-6":
            message += "4th"
        elif agent_name == "Agent-7":
            message += "5th"
        elif agent_name == "Agent-8":
            message += "6th"
            
        pyautogui.write(message)
        time.sleep(0.5)
        pyautogui.press('enter')
        
        logger.info(f"Sent initial message to {agent_name}")
        return True
    except Exception as e:
        logger.error(f"Error sending message to {agent_name}: {e}")
        return False

def main():
    """Main function to restart all agents and send initial messages."""
    logger.info("Starting Agent Restart System")
    
    # Sequence of agents
    agents = ["Agent-1", "Agent-2", "Agent-4", "Agent-6", "Agent-7", "Agent-8"]
    
    for agent in agents:
        logger.info(f"Processing {agent}")
        
        # Restart agent
        if restart_agent(agent):
            time.sleep(2)  # Wait for restart to complete
            
            # Send initial message
            if send_initial_message(agent):
                time.sleep(1)  # Wait between agents
            else:
                logger.error(f"Failed to send initial message to {agent}")
        else:
            logger.error(f"Failed to restart {agent}")
            
        # Wait between agents
        time.sleep(2)
    
    logger.info("Agent Restart System completed")

if __name__ == "__main__":
    main() 
