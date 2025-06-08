"""
Agent Control

Provides high-level control and management of agents in the system.
"""

import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class AgentControl:
    """High-level agent control and management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize agent control.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.agents: Dict[str, Any] = {}
        self.logger = logger
        
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register a new agent.
        
        Args:
            agent_id: Unique identifier for the agent
            agent: Agent instance to register
        """
        if agent_id in self.agents:
            raise ValueError(f"Agent {agent_id} already registered")
        self.agents[agent_id] = agent
        self.logger.info(f"Registered agent {agent_id}")
        
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent.
        
        Args:
            agent_id: ID of agent to unregister
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        del self.agents[agent_id]
        self.logger.info(f"Unregistered agent {agent_id}")
        
    def get_agent(self, agent_id: str) -> Any:
        """Get a registered agent.
        
        Args:
            agent_id: ID of agent to get
            
        Returns:
            Registered agent instance
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        return self.agents[agent_id]
        
    def list_agents(self) -> List[str]:
        """List all registered agent IDs.
        
        Returns:
            List of registered agent IDs
        """
        return list(self.agents.keys())
        
    def update_agent_config(self, agent_id: str, config: Dict[str, Any]) -> None:
        """Update an agent's configuration.
        
        Args:
            agent_id: ID of agent to update
            config: New configuration dictionary
        """
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        agent = self.agents[agent_id]
        if hasattr(agent, 'update_config'):
            agent.update_config(config)
        self.logger.info(f"Updated config for agent {agent_id}") 
