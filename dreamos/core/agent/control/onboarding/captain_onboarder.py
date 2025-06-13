"""
Captain Onboarder Module

Handles activation and onboarding of multiple agents by a captain agent.
Includes safety mechanisms to prevent self-onboarding and duplicate activations.
Supports any agent (1-8) as captain with proper network configuration.
"""

import asyncio
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from ..agent_operations import AgentOperations
from ..agent_status import AgentStatus
from ..agent_cellphone import AgentCellphone
from .message_manager import MessageManager

logger = logging.getLogger(__name__)

class CaptainOnboarder:
    """Handles activation and onboarding of multiple agents by a captain.
    
    Safety Features:
    - skip_self: Prevents the captain from onboarding itself
    - duplicate_check: Prevents re-onboarding already active agents
    - activation_tracking: Maintains record of which agents were activated
    - agent_validation: Ensures valid agent IDs and network configuration
    """
    
    # Valid agent ID pattern
    AGENT_ID_PATTERN = re.compile(r'^agent-([1-8])$')
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 cellphone: Optional[AgentCellphone] = None,
                 message_manager: Optional[MessageManager] = None):
        """Initialize the captain onboarder.
        
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
        self.activation_history: Dict[str, datetime] = {}
        
    def _validate_agent_id(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Validate an agent ID.
        
        Args:
            agent_id: Agent ID to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.AGENT_ID_PATTERN.match(agent_id):
            return False, f"Invalid agent ID format: {agent_id}. Must be agent-1 through agent-8"
        return True, None
        
    def _get_network_config(self, captain_id: str) -> Tuple[List[str], List[str]]:
        """Get network configuration for a given captain.
        
        Args:
            captain_id: ID of the captain agent
            
        Returns:
            Tuple of (all_agents, other_agents)
        """
        # Validate captain ID
        is_valid, error = self._validate_agent_id(captain_id)
        if not is_valid:
            raise ValueError(error)
            
        # Get captain number
        captain_num = int(captain_id.split('-')[1])
        
        # Create ordered list of all agents
        all_agents = [f"agent-{i+1}" for i in range(8)]
        
        # Create ordered list of other agents (excluding captain)
        other_agents = [aid for aid in all_agents if aid != captain_id]
        
        return all_agents, other_agents
        
    async def activate_agent_network(self, 
                                   captain_id: str,
                                   skip_self: bool = True,
                                   force: bool = False) -> bool:
        """Activate the entire agent network.
        
        Args:
            captain_id: ID of the captain agent (agent-1 through agent-8)
            skip_self: If True, captain will not onboard itself
            force: If True, will re-onboard already active agents
            
        Returns:
            bool: True if all agents activated successfully
            
        Raises:
            ValueError: If captain_id is invalid
        """
        try:
            # Validate captain ID
            is_valid, error = self._validate_agent_id(captain_id)
            if not is_valid:
                raise ValueError(error)
                
            logger.info(f"Captain {captain_id} initiating agent network activation")
            logger.info(f"skip_self={skip_self}, force={force}")
            
            # Get network configuration
            all_agents, other_agents = self._get_network_config(captain_id)
            agent_ids = other_agents if skip_self else all_agents
            
            if skip_self:
                logger.info(f"Skipping self-onboarding for captain {captain_id}")
                
            # Check for already active agents
            if not force:
                active_agents = []
                for agent_id in agent_ids:
                    status = await self.agent_status.get_agent_status(agent_id)
                    if status.get("status") == "active":
                        active_agents.append(agent_id)
                        logger.info(f"Skipping already active agent {agent_id}")
                agent_ids = [aid for aid in agent_ids if aid not in active_agents]
            
            if not agent_ids:
                logger.info("No agents need activation")
                return True
                
            # Create activation message
            activation_message = self.message_manager.create_network_activation_message(
                captain_id=captain_id,
                agent_ids=agent_ids,
                skip_self=skip_self
            )
            
            # Send activation message to each agent
            for agent_id in agent_ids:
                success = await self._activate_single_agent(agent_id, activation_message)
                if not success:
                    logger.error(f"Failed to activate {agent_id}")
                    return False
                self.activation_history[agent_id] = datetime.now()
                    
            logger.info("Agent network activation complete")
            return True
            
        except Exception as e:
            logger.error(f"Error activating agent network: {e}")
            return False
            
    async def _activate_single_agent(self, agent_id: str, message: str) -> bool:
        """Activate a single agent.
        
        Args:
            agent_id: ID of the agent to activate
            message: Activation message
            
        Returns:
            bool: True if activation successful
        """
        try:
            # Validate agent ID
            is_valid, error = self._validate_agent_id(agent_id)
            if not is_valid:
                logger.error(error)
                return False
                
            # Save message to inbox
            if not self.message_manager.save_message_to_inbox(agent_id, message):
                logger.error(f"Failed to save message to {agent_id}'s inbox")
                return False
                
            # Start agent onboarding
            await self.agent_ops.onboard_agent(agent_id, use_ui=True)
            
            # Wait for agent to be ready
            for _ in range(30):  # 30 second timeout
                status = await self.agent_status.get_agent_status(agent_id)
                if status.get("status") == "active":
                    logger.info(f"Agent {agent_id} activated successfully")
                    return True
                await asyncio.sleep(1)
                
            logger.error(f"Timeout waiting for {agent_id} to activate")
            return False
            
        except Exception as e:
            logger.error(f"Error activating {agent_id}: {e}")
            return False
            
    def get_activation_history(self) -> Dict[str, datetime]:
        """Get the activation history of agents.
        
        Returns:
            Dict mapping agent IDs to their activation timestamps
        """
        return self.activation_history.copy() 