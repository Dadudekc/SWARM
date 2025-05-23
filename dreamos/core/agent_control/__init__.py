"""
Agent Control Package

This package provides functionality for managing and controlling agents in the Dream.OS system.
"""

import logging
from typing import Dict, Callable
from PyQt5.QtWidgets import QApplication
from .controller import AgentController
from .menu_builder import MenuBuilder

logger = logging.getLogger(__name__)

# For backward compatibility
AgentCaptain = AgentController

def create_agent_control() -> AgentController:
    """Create and configure an agent controller instance."""
    # Create QApplication instance if it doesn't exist
    app = QApplication.instance()
    if not app:
        app = QApplication([])
    
    # Create controller
    controller = AgentController()
    
    # Map menu actions
    actions: Dict[str, Callable] = {
        'onboard_agent': controller.onboard_agent,
        'resume_agent': controller.resume_agent,
        'verify_agent': controller.verify_agent,
        'repair_agent': controller.repair_agent,
        'backup_agent': controller.backup_agent,
        'restore_agent': controller.restore_agent,
        'send_message': controller.send_message
    }
    
    # Create menu builder
    menu_builder = MenuBuilder(actions)
    controller.set_menu_builder(menu_builder)
    
    return controller

def main():
    """Main entry point for the agent control system."""
    try:
        controller = create_agent_control()
        controller.run()
    except KeyboardInterrupt:
        logger.info("Agent control system stopped by user")
    except Exception as e:
        logger.error(f"Error in agent control: {str(e)}")
        raise

if __name__ == "__main__":
    main()

__all__ = ['AgentController', 'AgentCaptain', 'MenuBuilder', 'create_agent_control', 'main'] 