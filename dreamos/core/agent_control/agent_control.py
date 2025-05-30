"""
Agent Control Module

Handles agent control operations including coordinate management and UI interactions.
"""

import logging
from pathlib import Path
import json
import pyautogui
from typing import Dict, Optional, Tuple

from .coordinate_transformer import CoordinateTransformer

logger = logging.getLogger('agent_control.agent_control')

class AgentControl:
    """Handles agent control operations."""
    
    def __init__(self, config_path: str):
        """Initialize agent control.
        
        Args:
            config_path: Path to coordinate configuration file
        """
        self.config_path = Path(config_path)
        self.transformer = CoordinateTransformer(transform_debug=True)
        self.coords = self._load_coordinates()
        
    def _load_coordinates(self) -> Dict:
        """Load coordinates from config file.
        
        Returns:
            Dictionary of agent coordinates
        """
        try:
            if not self.config_path.exists():
                logger.error(f"Coordinate file not found at {self.config_path}")
                return {}
                
            with open(self.config_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading coordinates: {e}")
            return {}
            
    def move_to_agent(self, agent_id: str) -> bool:
        """Move cursor to agent's initial position.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            coords = self.coords[agent_id]["initial_spot"]
            pyautogui.moveTo(coords["x"], coords["y"])
            return True
            
        except Exception as e:
            logger.error(f"Error moving to agent {agent_id}: {e}")
            return False
            
    def click_input_box(self, agent_id: str) -> bool:
        """Click agent's input box.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            coords = self.coords[agent_id]["input_box"]
            pyautogui.click(coords["x"], coords["y"])
            return True
            
        except Exception as e:
            logger.error(f"Error clicking input box for {agent_id}: {e}")
            return False
            
    def click_copy_button(self, agent_id: str) -> bool:
        """Click agent's copy button.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return False
                
            coords = self.coords[agent_id]["copy_button"]
            pyautogui.click(coords["x"], coords["y"])
            return True
            
        except Exception as e:
            logger.error(f"Error clicking copy button for {agent_id}: {e}")
            return False
            
    def get_response_region(self, agent_id: str) -> Optional[Dict]:
        """Get agent's response region coordinates.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Response region coordinates or None if not found
        """
        try:
            if agent_id not in self.coords:
                logger.error(f"No coordinates found for {agent_id}")
                return None
                
            if "response_region" not in self.coords[agent_id]:
                logger.error(f"No response region found for {agent_id}")
                return None
                
            return self.coords[agent_id]["response_region"]
            
        except Exception as e:
            logger.error(f"Error getting response region for {agent_id}: {e}")
            return None

def main():
    """Run agent control."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Control agent positioning")
    parser.add_argument("--config", default="runtime/config/cursor_agent_coords.json",
                      help="Path to coordinate configuration file")
    parser.add_argument("--agent", required=True,
                      help="ID of the agent to control")
    parser.add_argument("--action", choices=["move", "click_input", "click_copy", "get_region"],
                      required=True, help="Action to perform")
    args = parser.parse_args()
    
    control = AgentControl(args.config)
    
    if args.action == "move":
        success = control.move_to_agent(args.agent)
        print(f"Move to agent: {'Success' if success else 'Failed'}")
    elif args.action == "click_input":
        success = control.click_input_box(args.agent)
        print(f"Click input box: {'Success' if success else 'Failed'}")
    elif args.action == "click_copy":
        success = control.click_copy_button(args.agent)
        print(f"Click copy button: {'Success' if success else 'Failed'}")
    elif args.action == "get_region":
        region = control.get_response_region(args.agent)
        if region:
            print("\nResponse Region:")
            print(json.dumps(region, indent=2))
        else:
            print("Failed to get response region")

if __name__ == "__main__":
    main() 