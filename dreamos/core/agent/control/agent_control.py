"""
Agent Control Module

This module provides the core agent control functionality for Dream.OS.
It handles basic agent operations, status management, and control flow.
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..state import AgentState
from ..lifecycle import AgentManager

logger = logging.getLogger(__name__)

class AgentControl:
    """Base class for agent control functionality."""
    
    def __init__(self, agent_manager: AgentManager):
        """Initialize agent control.
        
        Args:
            agent_manager: The agent manager instance
        """
        self.agent_manager = agent_manager
        self._active_agents: Dict[str, AgentState] = {}
        
    def start_agent(self, agent_id: str) -> bool:
        """Start an agent.
        
        Args:
            agent_id: The ID of the agent to start
            
        Returns:
            bool: True if agent was started successfully
        """
        try:
            if agent_id in self._active_agents:
                logger.warning(f"Agent {agent_id} is already running")
                return False
                
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                logger.error(f"Agent {agent_id} not found")
                return False
                
            self._active_agents[agent_id] = agent
            logger.info(f"Started agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start agent {agent_id}: {str(e)}")
            return False
            
    def stop_agent(self, agent_id: str) -> bool:
        """Stop an agent.
        
        Args:
            agent_id: The ID of the agent to stop
            
        Returns:
            bool: True if agent was stopped successfully
        """
        try:
            if agent_id not in self._active_agents:
                logger.warning(f"Agent {agent_id} is not running")
                return False
                
            del self._active_agents[agent_id]
            logger.info(f"Stopped agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop agent {agent_id}: {str(e)}")
            return False
            
    def get_active_agents(self) -> List[str]:
        """Get list of active agent IDs.
        
        Returns:
            List[str]: List of active agent IDs
        """
        return list(self._active_agents.keys())
        
    def get_agent_status(self, agent_id: str) -> Optional[Dict]:
        """Get status of an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Optional[Dict]: Agent status info or None if agent not found
        """
        try:
            if agent_id not in self._active_agents:
                return None
                
            agent = self._active_agents[agent_id]
            return {
                'id': agent_id,
                'status': agent.status,
                'last_updated': datetime.now().isoformat(),
                'memory_usage': agent.memory_usage,
                'cpu_usage': agent.cpu_usage
            }
            
        except Exception as e:
            logger.error(f"Failed to get status for agent {agent_id}: {str(e)}")
            return None 
