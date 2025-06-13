"""
Agent Operations Module

This module provides core agent operations functionality for Dream.OS.
It handles basic agent operations, command execution, and state management.
"""

import logging
from typing import Union, List, Optional, Dict, Any
from pathlib import Path
import time
import uuid
from datetime import datetime

from ..messaging.message_processor import MessageProcessor
from ..messaging.common import MessageMode
from ..messaging.cell_phone import CellPhone
from .ui_automation import UIAutomation
from dreamos.core.config import ConfigManager
from ..state import AgentState
from ..lifecycle import AgentManager

logger = logging.getLogger(__name__)

class AgentOperations:
    """Core agent operations handler."""
    
    def __init__(self, agent_manager: AgentManager):
        """Initialize agent operations.
        
        Args:
            agent_manager: The agent manager instance
        """
        self.agent_manager = agent_manager
        self._operation_history: Dict[str, List[Dict[str, Any]]] = {}
        
    def execute_operation(self, agent_id: str, operation: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Execute an operation on an agent.
        
        Args:
            agent_id: The ID of the agent
            operation: The operation to execute
            params: Optional operation parameters
            
        Returns:
            bool: True if operation was executed successfully
        """
        try:
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return False
                
            # Execute operation
            result = agent.execute_operation(operation, params or {})
            
            # Record operation
            self._record_operation(agent_id, operation, params, result)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute operation on agent {agent_id}: {str(e)}")
            return False
            
    def get_operation_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get operation history for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            List[Dict[str, Any]]: List of operation records
        """
        return self._operation_history.get(agent_id, [])
        
    def clear_operation_history(self, agent_id: str) -> None:
        """Clear operation history for an agent.
        
        Args:
            agent_id: The ID of the agent
        """
        if agent_id in self._operation_history:
            del self._operation_history[agent_id]
            logger.info(f"Cleared operation history for agent {agent_id}")
            
    def _record_operation(self, agent_id: str, operation: str, params: Optional[Dict[str, Any]], result: Any) -> None:
        """Record an operation in history.
        
        Args:
            agent_id: The ID of the agent
            operation: The operation executed
            params: Operation parameters
            result: Operation result
        """
        if agent_id not in self._operation_history:
            self._operation_history[agent_id] = []
            
        record = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'params': params,
            'result': result
        }
        
        self._operation_history[agent_id].append(record)
        
        # Limit history size
        if len(self._operation_history[agent_id]) > 1000:
            self._operation_history[agent_id] = self._operation_history[agent_id][-1000:]

    async def _build_message(self, agent_id: str, content: str, task_id: str = "unknown") -> Dict[str, Any]:
        """Build a properly formatted message dictionary.
        
        Args:
            agent_id: The agent ID to send to
            content: The message content
            task_id: Optional task ID
            
        Returns:
            Formatted message dictionary
        """
        return {
            "type": "agent_message",
            "agent_id": agent_id,
            "content": content,
            "priority": "NORMAL",
            "task_id": task_id,
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }
        
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
        
    async def onboard_agent(self, agent_id: Union[str, List[str]], use_ui: bool = False) -> None:
        """Onboard a new agent.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            use_ui: Whether to use UI automation
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                await self._onboard_single_agent(aid, use_ui)
        else:
            await self._onboard_single_agent(agent_id, use_ui)

    async def _onboard_single_agent(self, agent_id: str, use_ui: bool = False) -> None:
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
            message_dict = await self._build_message(agent_id, message, "ONBOARD")
            await self.message_processor.send_message(message_dict)
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

    async def resume_agent(self, agent_id: Union[str, List[str]], use_ui: bool = False) -> bool:
        """Resume an agent's operation.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            use_ui: Whether to use UI automation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message for resuming
            message_dict = await self._build_message(agent_id, "Resume operations", "RESUME")
            await self.message_processor.send_message(message_dict)
            
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

    async def verify_agent(self, agent_id: Union[str, List[str]]) -> bool:
        """Verify an agent's status.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            
        Returns:
            True if verification successful, False otherwise
        """
        try:
            # Create message for verification
            message_dict = await self._build_message(agent_id, "Verify state", "VERIFY")
            await self.message_processor.send_message(message_dict)
            
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
            
    async def repair_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Repair an agent's issues.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                await self._repair_single_agent(aid)
        else:
            await self._repair_single_agent(agent_id)
            
    async def _repair_single_agent(self, agent_id: str) -> None:
        """Repair a single agent.
        
        Args:
            agent_id: The agent ID to repair
        """
        try:
            message = "Initiating repair sequence. Please follow the repair protocol."
            message_dict = await self._build_message(agent_id, message, "REPAIR")
            await self.message_processor.send_message(message_dict)
            logger.info(f"Repair message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error repairing agent {agent_id}: {e}")
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            
    async def backup_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Backup an agent's data.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                await self._backup_single_agent(aid)
        else:
            await self._backup_single_agent(agent_id)
            
    async def _backup_single_agent(self, agent_id: str) -> None:
        """Backup a single agent.
        
        Args:
            agent_id: The agent ID to backup
        """
        try:
            message = "Initiating backup sequence. Please prepare your data for backup."
            message_dict = await self._build_message(agent_id, message, "BACKUP")
            await self.message_processor.send_message(message_dict)
            logger.info(f"Backup message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error backing up agent {agent_id}: {e}")
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
            
    async def restore_agent(self, agent_id: Union[str, List[str]]) -> None:
        """Restore an agent from backup.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                await self._restore_single_agent(aid)
        else:
            await self._restore_single_agent(agent_id)
            
    async def _restore_single_agent(self, agent_id: str) -> None:
        """Restore a single agent.
        
        Args:
            agent_id: The agent ID to restore
        """
        try:
            message = "Initiating restore sequence. Please prepare to receive backup data."
            message_dict = await self._build_message(agent_id, message, "RESTORE")
            await self.message_processor.send_message(message_dict)
            logger.info(f"Restore message sent to agent {agent_id}")
        except Exception as e:
            logger.error(f"Error restoring agent {agent_id}: {e}")
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")

    async def send_message(self, agent_id: Union[str, List[str]], message: Optional[str] = None) -> None:
        """Send a message to one or more agents.
        
        Args:
            agent_id: Single agent ID or list of agent IDs
            message: Optional message content
        """
        if isinstance(agent_id, list):
            for aid in agent_id:
                await self._send_single_message(aid, message)
        else:
            await self._send_single_message(agent_id, message)

    async def _send_single_message(self, agent_id: str, message: str) -> None:
        """Send a message to a single agent.
        
        Args:
            agent_id: The agent ID to send to
            message: The message content
        """
        try:
            # Create message with correct format
            message_dict = await self._build_message(agent_id, message)
            
            # Send message
            await self.message_processor.send_message(message_dict)
            logger.info(f"Message sent to agent {agent_id}")
            
        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Error sending message to agent {agent_id}: {e}")
            
            # Try cell phone as fallback
            try:
                self.cell_phone.send_message(agent_id, message)
                logger.info(f"Fallback message sent via cell phone to {agent_id}")
            except Exception as cell_error:
                logger.error(f"Failed to send fallback message: {cell_error}")

    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if hasattr(self.message_processor, 'cleanup'):
                self.message_processor.cleanup()
            if hasattr(self.ui_automation, 'cleanup'):
                self.ui_automation.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}") 
