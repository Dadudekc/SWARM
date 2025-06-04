"""
Agent Operations Module

Handles all agent-specific operations like onboarding, resuming, etc.
"""

import logging
from typing import Union, List, Optional, Dict, Any
from pathlib import Path

from ..messaging.message_processor import MessageProcessor
from ..messaging.common import MessageMode
from ..cell_phone import CellPhone
from .ui_automation import UIAutomation

logger = logging.getLogger('agent_control.agent_operations')

class AgentOperations:
    """Handles agent-specific operations."""
    
    def __init__(self, runtime_dir: Optional[Path] = None):
        """Initialize agent operations.
        
        Args:
            runtime_dir: Optional runtime directory for message storage
        """
        if runtime_dir is None:
            runtime_dir = Path.home() / ".dreamos" / "runtime"
        self.runtime_dir = Path(runtime_dir)
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        
        self.message_processor = MessageProcessor(runtime_dir=self.runtime_dir)
        self.cell_phone = CellPhone()
        self.ui_automation = UIAutomation()
        self.last_error = None
        logger.info(f"Agent operations initialized with runtime dir: {self.runtime_dir}")
        
    def list_agents(self) -> List[str]:
        """List all available agents.
        
        Returns:
            List of agent IDs
        """
        try:
            # Get agents from coordinate manager if available
            if hasattr(self.message_processor, 'coordinate_manager') and self.message_processor.coordinate_manager:
                agents = list(self.message_processor.coordinate_manager.coordinates.keys())
                return sorted(agents)
            # Fallback: scan mailbox directory
            mailbox_path = getattr(self.message_processor, 'mailbox_path', None)
            if mailbox_path and mailbox_path.exists():
                return sorted([d.name for d in mailbox_path.iterdir() if d.is_dir()])
            else:
                logger.warning("Mailbox path not available or does not exist")
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
            # Load onboarding message
            message = self.ui_automation._load_onboarding_prompt(agent_id)

            # Send via UI if requested
            if use_ui:
                self.ui_automation.perform_onboarding_sequence(agent_id, message)

            # Always send via message processor
            self.message_processor.send_message(agent_id, message, "ONBOARD")
            logger.info(f"Onboarding message sent to agent {agent_id}")

        except Exception as e:
            error_msg = f"Error onboarding agent {agent_id}: {str(e)}"
            logger.error(error_msg)
            if hasattr(self.ui_automation, 'update_status'):
                self.ui_automation.update_status(error_msg)
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

    def resume_agent(self, agent_id: Union[str, List[str]], use_ui: bool = False) -> bool:
        """Resume an agent's operation.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            use_ui: Whether to use UI automation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message for resuming
            message = {
                "agent_id": agent_id,
                "type": "RESUME",
                "content": "Resume operations",
                "metadata": {"operation": "resume"}
            }
            
            # Send message
            self.message_processor.send_message(message)
            
            # Update UI
            self.ui_automation.click(agent_id)
            self.ui_automation.write("Resuming operations...")
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error resuming agent {agent_id}: {e}")
            
            # Send fallback message
            try:
                self.cell_phone.send_message(agent_id, "Fallback: Resume operations")
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as cell_error:
                logger.error(f"Failed to send fallback message: {cell_error}")
                
            return False

    def verify_agent(self, agent_id: Union[str, List[str]]) -> bool:
        """Verify an agent's status.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            # Create message for verification
            message = {
                "agent_id": agent_id,
                "type": "VERIFY",
                "content": "Verify state",
                "metadata": {"operation": "verify"}
            }
            
            # Send message
            self.message_processor.send_message(message)
            
            # Update UI
            self.ui_automation.click(agent_id)
            self.ui_automation.write("Verifying state...")
            
            return True
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error verifying agent {agent_id}: {e}")
            
            # Send fallback message
            try:
                self.cell_phone.send_message(agent_id, "Fallback: Verify state")
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as cell_error:
                logger.error(f"Failed to send fallback message: {cell_error}")
                
            return False
            
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
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            
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
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            
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
            message = "Initiating restore sequence. Please prepare for data restoration."
            self.message_processor.send_message(agent_id, message, "RESTORE")
            logger.info(f"Restore message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error restoring agent {agent_id}: {e}")
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            
    def send_message(self, agent_id: Union[str, List[str]], message: Optional[str] = None) -> None:
        """Send a message to an agent.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            message: Optional message to send
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                self._send_single_message(aid, message)
        else:
            self._send_single_message(agent_id, message)
            
    def _send_single_message(self, agent_id: str, message: str) -> None:
        """Send a message to a single agent.
        
        Args:
            agent_id: The agent ID to message
            message: The message to send
        """
        try:
            if not message:
                message = "Please check your status and report any issues."
                
            # Try message processor first
            self.message_processor.send_message(agent_id, message, "MESSAGE")
            logger.info(f"Message sent to agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error sending message to agent {agent_id}: {e}")
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            # Clean up message processor
            if hasattr(self.message_processor, 'cleanup'):
                self.message_processor.cleanup()
            
            # Clean up UI automation
            if hasattr(self.ui_automation, 'cleanup'):
                self.ui_automation.cleanup()
                
            logger.info("Agent operations cleaned up successfully")
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error during cleanup: {e}")
            raise 