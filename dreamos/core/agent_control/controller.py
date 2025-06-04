"""
Agent Controller Module

Main controller class for managing agent operations.
"""

import logging
from typing import Optional, Dict, Callable, Any, List
import pyautogui
import time
from pathlib import Path
import os

from .menu_builder import MenuBuilder
from .agent_operations import AgentOperations
from .ui_automation import UIAutomation
from ..messaging.message_processor import MessageProcessor
from ..cell_phone import CellPhone
from ..messaging.common import Message, MessageMode
from ..shared import CoordinateManager

logger = logging.getLogger('agent_control.controller')

class AgentController:
    """Main controller for agent operations."""
    
    def __init__(self, runtime_dir: Optional[str] = None):
        """Initialize the controller.
        
        Args:
            runtime_dir: Optional runtime directory path. If not provided,
                        will use a default location in the user's home directory.
        """
        self.logger = logging.getLogger('agent_controller')
        # Set up runtime directory
        if runtime_dir is None:
            runtime_dir = os.path.join(os.path.expanduser("~"), ".dreamos", "runtime")
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.agent_operations = AgentOperations(runtime_dir=str(self.runtime_dir))
        self.message_processor = MessageProcessor(runtime_dir=self.runtime_dir)
        self.cell_phone = CellPhone()  # CellPhone is a singleton, no parameters needed
        self.ui_automation = UIAutomation()  # Keep for visual feedback only
        self.menu_builder = None
        self._running = False
        self.coordinate_manager = CoordinateManager()
        
        # Initialize PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # Add small delay between actions
        
        logger.info(f"Agent controller initialized with runtime dir: {self.runtime_dir}")
        
    def set_menu_builder(self, menu_builder: MenuBuilder) -> None:
        """Set the menu builder and connect its signals.
        
        Args:
            menu_builder: The menu builder instance to use
        """
        self.menu_builder = menu_builder
        if self.menu_builder:
            self.menu_builder.menu.set_controller(self)
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
            'list': lambda: self._handle_list_agents(data),
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
                logger.error(f"Error executing action {item_id}: {e}")
                if self.menu_builder and self.menu_builder.menu:
                    self.menu_builder.menu._status_panel.update_status(f"Error: {str(e)}")
                
    def _handle_list_agents(self, agents: List[str] = None) -> None:
        """Handle list agents action.
        
        Args:
            agents: Optional list of agents to display
        """
        if agents is None:
            agents = self.list_agents()
            
        if agents:
            # Update status panel with agent list
            if self.menu_builder and self.menu_builder.menu:
                status_text = "Available agents:\n" + "\n".join(f"• {agent}" for agent in agents)
                self.menu_builder.menu._status_panel.update_status(status_text)
        else:
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status("No agents available")
            
    def cleanup(self) -> None:
        """Clean up all agent resources."""
        try:
            self.logger.info("Cleaning up agent resources")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status("Cleaning up...")
            
            # Clean up message processor
            self.agent_operations.message_processor.cleanup()
            
            # Clean up UI automation
            self.agent_operations.ui_automation.cleanup()
            
            # Remove all inbox files
            mailbox_dir = self.runtime_dir / "mailbox"
            for agent_dir in mailbox_dir.glob("Agent-*"):
                if agent_dir.is_dir():
                    for inbox in agent_dir.glob("*.json"):
                        if inbox.exists():
                            inbox.unlink()
            
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status("Cleanup complete")
            self.logger.info("Agent controller cleaned up successfully")
        except Exception as e:
            error_msg = f"Error during cleanup: {str(e)}"
            self.logger.error(error_msg)
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(error_msg)
        
    def run(self) -> None:
        """Run the controller."""
        try:
            self._running = True
            
            # Display and run the menu
            self.menu_builder.display_menu()
            if self.menu_builder.menu:
                # Keep a reference to the menu
                menu = self.menu_builder.menu
                # Run the menu event loop
                menu.run()
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.cleanup()
            
        except Exception as e:
            logger.error(f"Error in controller: {e}")
            self.cleanup()
            raise
            
        finally:
            # Ensure cleanup happens
            if self._running:
                self.cleanup()
        
    def list_agents(self) -> List[str]:
        """List all available agents.
        
        Returns:
            List of agent IDs
        """
        try:
            return self.agent_operations.list_agents()
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []
        
    def onboard_agent(self, agent_id: str, use_ui: bool = True) -> None:
        """Onboard a new agent using messaging system.
        
        Args:
            agent_id: The ID of the agent to onboard
            use_ui: Whether to use UI automation
        """
        if not agent_id:
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status("Error resuming : Invalid agent ID")
            return
            
        try:
            # Use agent operations for onboarding
            self.agent_operations.onboard_agent(agent_id)
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Onboarding {agent_id}...")
                
            logger.info(f"Onboarding {agent_id}")
            
        except Exception as e:
            logger.error(f"Error onboarding agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error onboarding {agent_id}: {str(e)}")
        
    def resume_agent(self, agent_id: str) -> bool:
        """Resume an agent's operations.
        
        Args:
            agent_id: ID of the agent to resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Resuming {agent_id}")
            self.menu_builder.menu._status_panel.update_status(f"Resuming {agent_id}...")
            
            # Attempt to resume agent
            success = self.agent_operations.resume_agent(agent_id)
            
            if not success:
                error_msg = f"Error resuming {agent_id}: {self.agent_operations.last_error}"
                self.logger.error(error_msg)
                self.menu_builder.menu._status_panel.update_status(error_msg)
                return False
                
            return True
            
        except Exception as e:
            error_msg = f"Error resuming {agent_id}: {str(e)}"
            self.logger.error(error_msg)
            self.menu_builder.menu._status_panel.update_status(error_msg)
            return False
        
    def verify_agent(self, agent_id: str) -> bool:
        """Verify an agent's state.
        
        Args:
            agent_id: ID of the agent to verify
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            self.logger.info(f"Verifying {agent_id}")
            self.menu_builder.menu._status_panel.update_status(f"Verifying {agent_id}...")
            
            # Attempt to verify agent
            success = self.agent_operations.verify_agent(agent_id)
            
            if not success:
                error_msg = f"Error verifying {agent_id}: {self.agent_operations.last_error}"
                self.logger.error(error_msg)
                self.menu_builder.menu._status_panel.update_status(error_msg)
                return False
                
            return True
            
        except Exception as e:
            error_msg = f"Error verifying {agent_id}: {str(e)}"
            self.logger.error(error_msg)
            self.menu_builder.menu._status_panel.update_status(error_msg)
            return False
        
    def repair_agent(self, agent_id: str) -> None:
        """Repair an agent using messaging system.
        
        Args:
            agent_id: The ID of the agent to repair
        """
        try:
            # Use agent operations for repair
            self.agent_operations.repair_agent(agent_id)
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Repairing {agent_id}...")
                
            logger.info(f"Repairing {agent_id}")
            
        except Exception as e:
            logger.error(f"Error repairing agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error repairing {agent_id}: {str(e)}")
        
    def backup_agent(self, agent_id: str) -> None:
        """Backup an agent using messaging system.
        
        Args:
            agent_id: The ID of the agent to backup
        """
        try:
            # Use agent operations for backup
            self.agent_operations.backup_agent(agent_id)
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Backing up {agent_id}...")
                
            logger.info(f"Backing up {agent_id}")
            
        except Exception as e:
            logger.error(f"Error backing up agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error backing up {agent_id}: {str(e)}")
        
    def restore_agent(self, agent_id: str) -> None:
        """Restore an agent using messaging system.
        
        Args:
            agent_id: The ID of the agent to restore
        """
        try:
            # Use agent operations for restore
            self.agent_operations.restore_agent(agent_id)
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Restoring {agent_id}...")
                
            logger.info(f"Restoring {agent_id}")
            
        except Exception as e:
            logger.error(f"Error restoring agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error restoring {agent_id}: {str(e)}")
        
    def send_message(self, agent_id: str) -> None:
        """Send a message to an agent using messaging system.
        
        Args:
            agent_id: The ID of the agent to message
        """
        try:
            # Get message from user
            message = input("\nEnter message: ").strip()
            if not message:
                logger.warning("Empty message, aborting")
                return
                
            # Use agent operations for sending message
            self.agent_operations.send_message(agent_id, message)
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Message sent to {agent_id}")
                
            logger.info(f"Message sent to {agent_id}")
            
        except Exception as e:
            logger.error(f"Error sending message to {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error sending message to {agent_id}: {str(e)}") 