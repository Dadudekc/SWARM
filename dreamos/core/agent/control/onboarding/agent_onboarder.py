"""
Agent Onboarder Module

Handles individual agent onboarding with consistent messaging and activation.
"""

import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime

from ..agent_operations import AgentOperations
from ..agent_status import AgentStatus
from ..agent_cellphone import AgentCellphone
from .message_manager import MessageManager

logger = logging.getLogger(__name__)

class AgentOnboarder:
    """Handles individual agent onboarding."""
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 cellphone: Optional[AgentCellphone] = None,
                 message_manager: Optional[MessageManager] = None):
        """Initialize the agent onboarder.
        
        Args:
            agent_ops: Agent operations interface
            agent_status: Agent status tracker
            cellphone: Optional agent cellphone instance
            message_manager: Optional message manager instance
        """
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.cellphone = cellphone or AgentCellphone()
        self.message_manager = message_manager or MessageManager()
        
    async def onboard_agent(self,
                          agent_id: str,
                          is_captain: bool = False,
                          use_ui: bool = True) -> bool:
        """Onboard a single agent.
        
        Args:
            agent_id: ID of the agent to onboard
            is_captain: Whether this agent is a captain
            use_ui: Whether to use UI automation
            
        Returns:
            bool: True if onboarding successful
        """
        try:
            logger.info(f"Starting onboarding for {agent_id}")
            
            # Create activation message
            activation_message = self.message_manager.create_individual_activation_message(
                agent_id=agent_id,
                is_captain=is_captain
            )
            
            # Save message to inbox
            if not self.message_manager.save_message_to_inbox(agent_id, activation_message):
                logger.error(f"Failed to save message to {agent_id}'s inbox")
                return False
                
            # Start agent onboarding
            await self.agent_ops.onboard_agent(agent_id, use_ui=use_ui)
            
            # Wait for agent to be ready
            for _ in range(30):  # 30 second timeout
                status = await self.agent_status.get_agent_status(agent_id)
                if status.get("status") == "active":
                    logger.info(f"Agent {agent_id} onboarded successfully")
                    return True
                await asyncio.sleep(1)
                
            logger.error(f"Timeout waiting for {agent_id} to activate")
            return False
            
        except Exception as e:
            logger.error(f"Error onboarding {agent_id}: {e}")
            return False 