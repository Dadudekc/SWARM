"""
Agent Controller Module

Main controller class for managing agent operations.
"""

import logging
from typing import Optional, Dict, Callable, Any, List
import pyautogui
import time

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
        self._running = False
        
        # Initialize PyAutoGUI settings
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.5  # Add small delay between actions
        
    def set_menu_builder(self, menu_builder: MenuBuilder) -> None:
        """Set the menu builder and connect its signals.
        
        Args:
            menu_builder: The menu builder instance to use
        """
        self.menu_builder = menu_builder
        if self.menu_builder:
            self.menu_builder.menu.set_controller(self)  # Set controller reference
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
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self._running = False
            
            # Disconnect signals
            if self.menu_builder:
                self.menu_builder.disconnect_signals()
                
            # Clean up agent operations
            if self.agent_operations:
                try:
                    self.agent_operations.cleanup()
                except AttributeError:
                    pass  # Ignore if cleanup method doesn't exist
                
            # Clean up UI automation
            if self.ui_automation:
                try:
                    self.ui_automation.cleanup()
                except AttributeError:
                    pass  # Ignore if cleanup method doesn't exist
                
            logger.info("Agent controller cleaned up successfully")
            
        except Exception as e:
            logger.error(f"Error during controller cleanup: {e}")
            
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
            # Get agent coordinates from UI automation
            coords = self.ui_automation.get_agent_coordinates()
            return sorted(coords.keys()) if coords else []
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []
        
    def onboard_agent(self, agent_id: str) -> None:
        """Onboard a new agent using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to onboard
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)  # Wait for movement
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)  # Wait for selection
            
            # Move to onboard button
            pyautogui.moveTo(agent_coords['onboard_x'], agent_coords['onboard_y'])
            time.sleep(0.5)  # Wait for movement
            
            # Click onboard button
            pyautogui.click()
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Onboarding {agent_id}...")
                
            logger.info(f"Onboarding {agent_id}")
            
        except Exception as e:
            logger.error(f"Error onboarding agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error onboarding {agent_id}: {str(e)}")
        
    def resume_agent(self, agent_id: str) -> None:
        """Resume an agent's operation using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to resume
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)
            
            # Move to resume button
            pyautogui.moveTo(agent_coords['resume_x'], agent_coords['resume_y'])
            time.sleep(0.5)
            
            # Click resume button
            pyautogui.click()
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Resuming {agent_id}...")
                
            logger.info(f"Resuming {agent_id}")
            
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error resuming {agent_id}: {str(e)}")
        
    def verify_agent(self, agent_id: str) -> None:
        """Verify an agent's state using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to verify
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)
            
            # Move to verify button
            pyautogui.moveTo(agent_coords['verify_x'], agent_coords['verify_y'])
            time.sleep(0.5)
            
            # Click verify button
            pyautogui.click()
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Verifying {agent_id}...")
                
            logger.info(f"Verifying {agent_id}")
            
        except Exception as e:
            logger.error(f"Error verifying agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error verifying {agent_id}: {str(e)}")
        
    def repair_agent(self, agent_id: str) -> None:
        """Repair an agent's issues using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to repair
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)
            
            # Move to repair button
            pyautogui.moveTo(agent_coords['repair_x'], agent_coords['repair_y'])
            time.sleep(0.5)
            
            # Click repair button
            pyautogui.click()
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Repairing {agent_id}...")
                
            logger.info(f"Repairing {agent_id}")
            
        except Exception as e:
            logger.error(f"Error repairing agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error repairing {agent_id}: {str(e)}")
        
    def backup_agent(self, agent_id: str) -> None:
        """Backup an agent's data using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to backup
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)
            
            # Move to backup button
            pyautogui.moveTo(agent_coords['backup_x'], agent_coords['backup_y'])
            time.sleep(0.5)
            
            # Click backup button
            pyautogui.click()
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Backing up {agent_id}...")
                
            logger.info(f"Backing up {agent_id}")
            
        except Exception as e:
            logger.error(f"Error backing up agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error backing up {agent_id}: {str(e)}")
        
    def restore_agent(self, agent_id: str) -> None:
        """Restore an agent from backup using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to restore
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)
            
            # Move to restore button
            pyautogui.moveTo(agent_coords['restore_x'], agent_coords['restore_y'])
            time.sleep(0.5)
            
            # Click restore button
            pyautogui.click()
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Restoring {agent_id}...")
                
            logger.info(f"Restoring {agent_id}")
            
        except Exception as e:
            logger.error(f"Error restoring agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error restoring {agent_id}: {str(e)}")
        
    def send_message(self, agent_id: str) -> None:
        """Send a message to an agent using PyAutoGUI.
        
        Args:
            agent_id: The ID of the agent to message
        """
        try:
            # Get agent coordinates
            coords = self.ui_automation.get_agent_coordinates()
            if agent_id not in coords:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Get coordinates for the agent
            agent_coords = coords[agent_id]
            
            # Move to agent position
            pyautogui.moveTo(agent_coords['x'], agent_coords['y'])
            time.sleep(0.5)
            
            # Click to select agent
            pyautogui.click()
            time.sleep(0.5)
            
            # Move to message input
            pyautogui.moveTo(agent_coords['message_x'], agent_coords['message_y'])
            time.sleep(0.5)
            
            # Click to focus input
            pyautogui.click()
            time.sleep(0.5)
            
            # Type message
            pyautogui.write("Test message")
            time.sleep(0.5)
            
            # Press enter to send
            pyautogui.press('enter')
            
            # Update status
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Message sent to {agent_id}")
                
            logger.info(f"Message sent to {agent_id}")
            
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {e}")
            if self.menu_builder and self.menu_builder.menu:
                self.menu_builder.menu._status_panel.update_status(f"Error sending message to {agent_id}: {str(e)}") 