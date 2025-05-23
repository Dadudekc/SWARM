"""
Agent Operations Module

Handles all agent-specific operations like onboarding, resuming, etc.
"""

import logging
from typing import Union, List, Optional

from ..message_processor import MessageProcessor
from ..cell_phone import CellPhone
from .ui_automation import UIAutomation

logger = logging.getLogger('agent_control.agent_operations')

class AgentOperations:
    """Handles agent-specific operations."""
    
    def __init__(self):
        """Initialize agent operations."""
        self.message_processor = MessageProcessor()
        self.cell_phone = CellPhone()
        self.ui_automation = UIAutomation()
        
    def list_agents(self) -> List[str]:
        """List all available agents.
        
        Returns:
            List of agent IDs
        """
        try:
            # Get agents from coordinate manager
            if hasattr(self.message_processor, 'coordinate_manager'):
                agents = list(self.message_processor.coordinate_manager.coordinates.keys())
                return agents
            else:
                logger.warning("Coordinate manager not available")
                return []
        except Exception as e:
            logger.error(f"Error listing agents: {e}")
            return []
        
    def onboard_agent(self, agent_id: Union[str, List[str]], use_ui: bool = False) -> None:
        """Onboard a new agent.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            use_ui: Whether to use UI automation
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._onboard_single_agent(aid, use_ui)
        else:
            self._onboard_single_agent(agent_id, use_ui)

    def _onboard_single_agent(self, agent_id: str, use_ui: bool = False) -> None:
        """Onboard a single agent.
        
        Args:
            agent_id: The agent ID to onboard
            use_ui: Whether to use UI automation
        """
        try:
            message = """Welcome to Dream.OS! You are now part of our agent network.
                
Your initial tasks:
1. Initialize your core systems
2. Establish communication channels
3. Begin monitoring your assigned domain
4. Report your status when ready

Let's begin your integration into the Dream.OS ecosystem."""

            if use_ui:
                self.ui_automation.perform_onboarding_sequence(agent_id, message)

            # Always send via message processor as well
            self.message_processor.send_message(agent_id, message, "ONBOARD")
            logger.info(f"Onboarding message sent to agent {agent_id}")

        except Exception as e:
            logger.error(f"Error onboarding agent {agent_id}: {e}")
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

    def resume_agent(self, agent_id: Union[str, List[str]], use_ui: bool = False) -> None:
        """Resume an agent's operation.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            use_ui: Whether to use UI automation
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._resume_single_agent(aid, use_ui)
        else:
            self._resume_single_agent(agent_id, use_ui)

    def _resume_single_agent(self, agent_id: str, use_ui: bool = False) -> None:
        """Resume a single agent.
        
        Args:
            agent_id: The agent ID to resume
            use_ui: Whether to use UI automation
        """
        try:
            message = "Resuming operations. Please confirm your status and continue with assigned tasks."
            
            if use_ui:
                self.ui_automation.send_message(agent_id, message)
            else:
                self.message_processor.send_message(agent_id, message, "RESUME")
                
            logger.info(f"Resume message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")

    def verify_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Verify an agent's status.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._verify_single_agent(aid)
        else:
            self._verify_single_agent(agent_id)
            
    def _verify_single_agent(self, agent_id: str) -> None:
        """Verify a single agent.
        
        Args:
            agent_id: The agent ID to verify
        """
        try:
            message = "Please verify your status and report any issues."
            self.message_processor.send_message(agent_id, message, "VERIFY")
            logger.info(f"Verify message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error verifying agent {agent_id}: {e}")
            
    def repair_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Repair an agent's issues.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._repair_single_agent(aid)
        else:
            self._repair_single_agent(agent_id)
            
    def _repair_single_agent(self, agent_id: str) -> None:
        """Repair a single agent.
        
        Args:
            agent_id: The agent ID to repair
        """
        try:
            message = "Initiating repair sequence. Please follow the repair protocol."
            self.message_processor.send_message(agent_id, message, "REPAIR")
            logger.info(f"Repair message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error repairing agent {agent_id}: {e}")
            
    def backup_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Backup an agent's data.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._backup_single_agent(aid)
        else:
            self._backup_single_agent(agent_id)
            
    def _backup_single_agent(self, agent_id: str) -> None:
        """Backup a single agent.
        
        Args:
            agent_id: The agent ID to backup
        """
        try:
            message = "Initiating backup sequence. Please prepare your data for backup."
            self.message_processor.send_message(agent_id, message, "BACKUP")
            logger.info(f"Backup message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error backing up agent {agent_id}: {e}")
            
    def restore_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Restore an agent from backup.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._restore_single_agent(aid)
        else:
            self._restore_single_agent(agent_id)
            
    def _restore_single_agent(self, agent_id: str) -> None:
        """Restore a single agent.
        
        Args:
            agent_id: The agent ID to restore
        """
        try:
            message = "Initiating restore sequence. Please prepare to receive backup data."
            self.message_processor.send_message(agent_id, message, "RESTORE")
            logger.info(f"Restore message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error restoring agent {agent_id}: {e}")
            
    def send_message(self, agent_id: Union[str, List[str]], message: Optional[str] = None) -> None:
        """Send a message to agent(s).
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            message: Optional message to send. If None, will prompt for input.
        """
        if message is None:
            message = input("\nEnter message: ").strip()
            if not message:
                logger.warning("Empty message, aborting")
                return
            
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._send_single_message(aid, message)
        else:
            self._send_single_message(agent_id, message)
            
    def _send_single_message(self, agent_id: str, message: str) -> None:
        """Send a message to a single agent.
        
        Args:
            agent_id: The agent ID to send to
            message: The message content
        """
        try:
            self.message_processor.send_message(agent_id, message, "NORMAL")
            logger.info(f"Message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {e}") 