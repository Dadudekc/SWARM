"""
Agent Status Module

This module provides comprehensive agent status tracking and monitoring functionality for Dream.OS.
It handles status tracking, health checks, performance monitoring, and status serialization.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime
import psutil

from ..state import AgentState
from ..lifecycle import AgentManager

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Enum representing possible agent states."""
    
    INITIALIZING = auto()
    IDLE = auto()
    BUSY = auto()
    ERROR = auto()
    SHUTDOWN = auto()

class AgentStatusInfo:
    """Class for tracking detailed agent status information."""
    
    def __init__(self, 
                 status: AgentStatus = AgentStatus.INITIALIZING,
                 last_updated: Optional[datetime] = None,
                 error_message: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        """Initialize agent status info.
        
        Args:
            status: Current agent status
            last_updated: Timestamp of last status update
            error_message: Optional error message if status is ERROR
            metadata: Optional additional status metadata
        """
        self.status = status
        self.last_updated = last_updated or datetime.utcnow()
        self.error_message = error_message
        self.metadata = metadata or {}
        
    def update(self,
              status: Optional[AgentStatus] = None,
              error_message: Optional[str] = None,
              metadata: Optional[Dict[str, Any]] = None) -> None:
        """Update agent status information.
        
        Args:
            status: New status to set
            error_message: New error message to set
            metadata: New metadata to set
        """
        if status is not None:
            self.status = status
        if error_message is not None:
            self.error_message = error_message
        if metadata is not None:
            self.metadata.update(metadata)
        self.last_updated = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert status info to dictionary.
        
        Returns:
            Dictionary representation of status info
        """
        return {
            'status': self.status.name,
            'last_updated': self.last_updated.isoformat(),
            'error_message': self.error_message,
            'metadata': self.metadata
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentStatusInfo':
        """Create AgentStatusInfo from dictionary.
        
        Args:
            data: Dictionary containing status info
            
        Returns:
            New AgentStatusInfo instance
        """
        return cls(
            status=AgentStatus[data['status']],
            last_updated=datetime.fromisoformat(data['last_updated']),
            error_message=data.get('error_message'),
            metadata=data.get('metadata', {})
        )

class AgentStatusTracker:
    """Agent status tracking and monitoring."""
    
    def __init__(self, agent_manager: AgentManager):
        """Initialize agent status tracking.
        
        Args:
            agent_manager: The agent manager instance
        """
        self.agent_manager = agent_manager
        self._status_history: Dict[str, List[AgentStatusInfo]] = {}
        self._health_checks: Dict[str, List[Dict[str, Any]]] = {}
        
    def update_status(self, agent_id: str, status: AgentStatus, details: Optional[Dict[str, Any]] = None) -> None:
        """Update agent status.
        
        Args:
            agent_id: The ID of the agent
            status: New status
            details: Optional status details
        """
        try:
            if agent_id not in self._status_history:
                self._status_history[agent_id] = []
                
            status_info = AgentStatusInfo(
                status=status,
                metadata=details
            )
            
            self._status_history[agent_id].append(status_info)
            
            # Limit history size
            if len(self._status_history[agent_id]) > 1000:
                self._status_history[agent_id] = self._status_history[agent_id][-1000:]
                
            logger.info(f"Updated status for agent {agent_id}: {status.name}")
            
        except Exception as e:
            logger.error(f"Failed to update status for agent {agent_id}: {str(e)}")
            
    def get_current_status(self, agent_id: str) -> Optional[AgentStatusInfo]:
        """Get current status for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Optional[AgentStatusInfo]: Current status info or None if not found
        """
        try:
            if agent_id not in self._status_history or not self._status_history[agent_id]:
                return None
                
            return self._status_history[agent_id][-1]
            
        except Exception as e:
            logger.error(f"Failed to get status for agent {agent_id}: {str(e)}")
            return None
            
    def get_status_history(self, agent_id: str) -> List[AgentStatusInfo]:
        """Get status history for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            List[AgentStatusInfo]: List of status records
        """
        return self._status_history.get(agent_id, [])
        
    def run_health_check(self, agent_id: str) -> Dict[str, Any]:
        """Run health check for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            Dict[str, Any]: Health check results
        """
        try:
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                return {
                    'status': 'error',
                    'message': f'Agent {agent_id} not found',
                    'timestamp': datetime.now().isoformat()
                }
                
            # Get process info
            process = psutil.Process(agent.pid)
            
            health_info = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'cpu_percent': process.cpu_percent(),
                'memory_percent': process.memory_percent(),
                'memory_rss': process.memory_info().rss,
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
            
            # Record health check
            if agent_id not in self._health_checks:
                self._health_checks[agent_id] = []
                
            self._health_checks[agent_id].append(health_info)
            
            # Limit history size
            if len(self._health_checks[agent_id]) > 100:
                self._health_checks[agent_id] = self._health_checks[agent_id][-100:]
                
            return health_info
            
        except Exception as e:
            logger.error(f"Failed to run health check for agent {agent_id}: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    def get_health_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get health check history for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            List[Dict[str, Any]]: List of health check records
        """
        return self._health_checks.get(agent_id, []) 