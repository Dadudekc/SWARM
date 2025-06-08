"""
Response Tracker Module

Tracks and manages agent responses, including message history and status updates.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AgentResponseTracker:
    """Tracks agent responses and message history."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the response tracker.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.response_history: Dict[str, List[Dict]] = {}
        self.last_response_time: Dict[str, datetime] = {}
        
    async def track_response(self, agent_id: str, response: str, status: str = "success") -> None:
        """Track a new response from an agent.
        
        Args:
            agent_id: ID of the agent
            response: The response content
            status: Response status (success/error)
        """
        try:
            if agent_id not in self.response_history:
                self.response_history[agent_id] = []
                
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "response": response,
                "status": status
            }
            
            self.response_history[agent_id].append(entry)
            self.last_response_time[agent_id] = datetime.utcnow()
            
            # Trim history if too long
            max_history = self.config.get("max_response_history", 100)
            if len(self.response_history[agent_id]) > max_history:
                self.response_history[agent_id] = self.response_history[agent_id][-max_history:]
                
        except Exception as e:
            logger.error(f"Error tracking response for agent {agent_id}: {e}")
            
    async def get_response_history(self, agent_id: str, limit: Optional[int] = None) -> List[Dict]:
        """Get response history for an agent.
        
        Args:
            agent_id: ID of the agent
            limit: Optional limit on number of responses to return
            
        Returns:
            List of response entries
        """
        try:
            history = self.response_history.get(agent_id, [])
            if limit:
                history = history[-limit:]
            return history
        except Exception as e:
            logger.error(f"Error getting response history for agent {agent_id}: {e}")
            return []
            
    async def get_last_response_time(self, agent_id: str) -> Optional[datetime]:
        """Get the timestamp of the last response from an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Timestamp of last response, or None if no responses
        """
        return self.last_response_time.get(agent_id)
        
    async def clear_history(self, agent_id: str) -> None:
        """Clear response history for an agent.
        
        Args:
            agent_id: ID of the agent
        """
        try:
            if agent_id in self.response_history:
                self.response_history[agent_id] = []
            if agent_id in self.last_response_time:
                del self.last_response_time[agent_id]
        except Exception as e:
            logger.error(f"Error clearing history for agent {agent_id}: {e}")
            
    async def save_history(self, file_path: str) -> bool:
        """Save response history to a file.
        
        Args:
            file_path: Path to save history to
            
        Returns:
            True if save successful
        """
        try:
            data = {
                "response_history": self.response_history,
                "last_response_time": {
                    k: v.isoformat() for k, v in self.last_response_time.items()
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
            
        except Exception as e:
            logger.error(f"Error saving response history: {e}")
            return False
            
    async def load_history(self, file_path: str) -> bool:
        """Load response history from a file.
        
        Args:
            file_path: Path to load history from
            
        Returns:
            True if load successful
        """
        try:
            if not Path(file_path).exists():
                return False
                
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            self.response_history = data["response_history"]
            self.last_response_time = {
                k: datetime.fromisoformat(v)
                for k, v in data["last_response_time"].items()
            }
            return True
            
        except Exception as e:
            logger.error(f"Error loading response history: {e}")
            return False 