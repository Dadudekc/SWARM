"""
Agent Controller Module
---------------------
Manages agent lifecycle and coordination.
"""

from typing import Dict, Any, Optional
from pathlib import Path

from dreamos.core.shared.coordinate_manager import CoordinateManager
from dreamos.core.logging.agent_logger import AgentLogger
from dreamos.core.config.config_manager import ConfigManager

class AgentController:
    """Manages agent lifecycle and coordination."""
    
    def __init__(self, config: Optional[ConfigManager] = None):
        """Initialize the agent controller.
        
        Args:
            config: Optional config manager instance
        """
        self.config = config or ConfigManager()
        self.coordinate_manager = CoordinateManager()
        self.logger = AgentLogger()
        
    def get_agent(self, agent_id: str) -> Any:
        """Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get
            
        Returns:
            The agent instance
        """
        return self.coordinate_manager.get_agent(agent_id)
        
    def register_agent(self, agent_id: str, agent: Any) -> None:
        """Register a new agent.
        
        Args:
            agent_id: The ID of the agent
            agent: The agent instance
        """
        self.coordinate_manager.register_agent(agent_id, agent)
        
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent.
        
        Args:
            agent_id: The ID of the agent to unregister
        """
        self.coordinate_manager.unregister_agent(agent_id) 