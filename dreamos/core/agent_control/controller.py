"""
Agent Controller Module

Main controller class for managing agent operations.
"""

import logging
from typing import Optional, Dict, Callable, Any, List

from .menu_builder import MenuBuilder
from .agent_operations import AgentOperations
from .ui_automation import UIAutomation

logger = logging.getLogger('agent_control.controller')

class AgentController:
    """Main controller for agent operations."""
    
    def __init__(self):
        """Initialize the controller."""
        self.agent_operations = AgentOperations()
        self.ui_automation = UIAutomation()
        self.menu_builder = None  # Will be set by set_menu_builder
        
    def set_menu_builder(self, menu_builder: MenuBuilder) -> None:
        """Set the menu builder and connect its signals.
        
        Args:
            menu_builder: The menu builder instance to use
        """
        self.menu_builder = menu_builder
        if self.menu_builder:
            self.menu_builder.connect_signals(self._handle_menu_action)
        
    def _handle_menu_action(self, item_id: str, data: Any) -> None:
        """Handle menu item selection.
        
        Args:
            item_id: ID of the selected menu item
            data: Additional data (e.g. selected agent)
        """
        logger.debug(f"Menu action: {item_id} with data: {data}")
        
        # Map item IDs to actions
        action_map = {
            'list': lambda: self.list_agents(),
            'onboard': lambda: self.onboard_agent(data) if data else None,
            'resume': lambda: self.resume_agent(data) if data else None,
            'verify': lambda: self.verify_agent(data) if data else None,
            'repair': lambda: self.repair_agent(data) if data else None,
            'backup': lambda: self.backup_agent(data) if data else None,
            'restore': lambda: self.restore_agent(data) if data else None,
            'message': lambda: self.send_message(data) if data else None
        }
        
        # Execute the action if it exists
        if item_id in action_map:
            try:
                action_map[item_id]()
            except Exception as e:
                logger.error(f"Error executing menu action {item_id}: {e}")
                # TODO: Show error in UI
                
    def run(self) -> None:
        """Run the controller."""
        try:
            # Display and run the menu
            self.menu_builder.display_menu()
            if self.menu_builder.menu:
                # Keep a reference to the menu
                menu = self.menu_builder.menu
                # Run the menu event loop
                menu.run()
        except Exception as e:
            logger.error(f"Error in controller: {e}")
            raise
        finally:
            # Clean up
            if self.menu_builder:
                try:
                    self.menu_builder.disconnect_signals()
                except Exception as e:
                    logger.error(f"Error during cleanup: {e}")
            
    def list_agents(self) -> List[str]:
        """List all available agents.
        
        Returns:
            List of agent IDs
        """
        return self.agent_operations.list_agents()
        
    def onboard_agent(self, agent_id: str) -> None:
        """Onboard a new agent.
        
        Args:
            agent_id: The ID of the agent to onboard
        """
        self.agent_operations.onboard_agent(agent_id)
        
    def resume_agent(self, agent_id: str) -> None:
        """Resume an agent's operation.
        
        Args:
            agent_id: The ID of the agent to resume
        """
        self.agent_operations.resume_agent(agent_id)
        
    def verify_agent(self, agent_id: str) -> None:
        """Verify an agent's state.
        
        Args:
            agent_id: The ID of the agent to verify
        """
        self.agent_operations.verify_agent(agent_id)
        
    def repair_agent(self, agent_id: str) -> None:
        """Repair an agent's issues.
        
        Args:
            agent_id: The ID of the agent to repair
        """
        self.agent_operations.repair_agent(agent_id)
        
    def backup_agent(self, agent_id: str) -> None:
        """Backup an agent's data.
        
        Args:
            agent_id: The ID of the agent to backup
        """
        self.agent_operations.backup_agent(agent_id)
        
    def restore_agent(self, agent_id: str) -> None:
        """Restore an agent from backup.
        
        Args:
            agent_id: The ID of the agent to restore
        """
        self.agent_operations.restore_agent(agent_id)
        
    def send_message(self, agent_id: str) -> None:
        """Send a message to an agent.
        
        Args:
            agent_id: The ID of the agent to message
        """
        # TODO: Implement message dialog/input
        logger.info(f"Sending message to agent {agent_id}")
        # For now, just log the action
        self.agent_operations.send_message(
            agent_id,
            "Test message",
            priority="normal",
            mode="text"
        ) 