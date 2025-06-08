"""
Agent State Management
-------------------
Manages agent states and provides auto-resume functionality.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AgentState:
    """Manages agent states and provides auto-resume functionality."""
    
    # Agent states
    IDLE = "idle"
    PROCESSING = "processing"
    RESUMING = "resuming"
    ERROR = "error"
    
    # Auto-resume settings
    IDLE_TIMEOUT = timedelta(minutes=5)  # Consider agent stuck after 5 minutes idle
    
    def __init__(self):
        """Initialize the agent state manager."""
        self.agents: Dict[str, Dict] = {}  # agent_id -> state_data
    
    def update_agent_state(self, agent_id: str, state: str) -> None:
        """Update an agent's state.
        
        Args:
            agent_id: Agent identifier
            state: New state
        """
        if agent_id not in self.agents:
            self.agents[agent_id] = {
                "state": state,
                "last_update": datetime.utcnow(),
                "history": []
            }
        else:
            # Add to history
            self.agents[agent_id]["history"].append({
                "state": self.agents[agent_id]["state"],
                "timestamp": self.agents[agent_id]["last_update"]
            })
            # Update current state
            self.agents[agent_id]["state"] = state
            self.agents[agent_id]["last_update"] = datetime.utcnow()
    
    def get_agent_state(self, agent_id: str) -> Optional[str]:
        """Get an agent's current state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current state or None if agent not found
        """
        return self.agents.get(agent_id, {}).get("state")
    
    def get_idle_agents(self) -> List[str]:
        """Get list of idle agents.
        
        Returns:
            List of agent IDs that are idle
        """
        return [
            agent_id for agent_id, data in self.agents.items()
            if data["state"] == self.IDLE
        ]
    
    def is_agent_stuck(self, agent_id: str) -> bool:
        """Check if an agent is stuck (idle too long).
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent is stuck, False otherwise
        """
        agent_data = self.agents.get(agent_id)
        if not agent_data or agent_data["state"] != self.IDLE:
            return False
        
        idle_time = datetime.utcnow() - agent_data["last_update"]
        return idle_time > self.IDLE_TIMEOUT
    
    def get_agent_stats(self, agent_id: str) -> Dict:
        """Get agent statistics.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary of agent statistics
        """
        agent_data = self.agents.get(agent_id, {})
        return {
            "current_state": agent_data.get("state"),
            "last_update": agent_data.get("last_update"),
            "history": agent_data.get("history", []),
            "is_stuck": self.is_agent_stuck(agent_id) if agent_id in self.agents else False
        }
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all agents.
        
        Returns:
            Dictionary mapping agent IDs to their statistics
        """
        return {
            agent_id: self.get_agent_stats(agent_id)
            for agent_id in self.agents
        } 
