"""
Agent Restarter Module

This module provides agent restart and recovery functionality for Dream.OS.
It handles agent restart operations, recovery strategies, and failure handling.
"""

from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime, timedelta

from ..state import AgentState
from ..lifecycle import AgentManager
from .agent_status import AgentStatus, AgentStatusInfo, AgentStatusTracker
from .agent_operations import AgentOperations

logger = logging.getLogger(__name__)

class AgentRestarter:
    """Agent restart and recovery management."""
    
    def __init__(self, 
                 agent_manager: AgentManager,
                 max_retries: int = 3,
                 retry_delay: int = 60,
                 recovery_timeout: int = 300):
        """Initialize agent restarter.
        
        Args:
            agent_manager: The agent manager instance
            max_retries: Maximum number of restart attempts
            retry_delay: Delay between restart attempts in seconds
            recovery_timeout: Maximum time for recovery in seconds
        """
        self.agent_manager = agent_manager
        self.status_tracker = AgentStatusTracker(agent_manager)
        self.operations = AgentOperations(agent_manager)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.recovery_timeout = recovery_timeout
        self._restart_history: Dict[str, List[Dict[str, Any]]] = {}
        
    async def restart_agent(self, agent_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Restart an agent with recovery.
        
        Args:
            agent_id: The ID of the agent
            reason: Optional reason for restart
            
        Returns:
            Dict[str, Any]: Restart result
        """
        try:
            agent = self.agent_manager.get_agent(agent_id)
            if not agent:
                raise ValueError(f"Agent {agent_id} not found")
                
            # Record restart attempt
            if agent_id not in self._restart_history:
                self._restart_history[agent_id] = []
                
            attempt = {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'status': 'in_progress'
            }
            self._restart_history[agent_id].append(attempt)
            
            # Limit history size
            if len(self._restart_history[agent_id]) > 100:
                self._restart_history[agent_id] = self._restart_history[agent_id][-100:]
                
            # Attempt restart with recovery
            success = await self._attempt_restart(agent_id)
            
            # Update attempt record
            attempt['status'] = 'success' if success else 'failed'
            attempt['completed_at'] = datetime.now().isoformat()
            
            return {
                'status': 'success' if success else 'error',
                'message': f'Agent {agent_id} {"restarted successfully" if success else "failed to restart"}',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restart agent {agent_id}: {str(e)}")
            if attempt:
                attempt['status'] = 'failed'
                attempt['error'] = str(e)
                attempt['completed_at'] = datetime.now().isoformat()
                
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
            
    async def _attempt_restart(self, agent_id: str) -> bool:
        """Attempt to restart an agent with recovery.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            bool: True if restart was successful
        """
        start_time = datetime.now()
        retry_count = 0
        
        while retry_count < self.max_retries:
            try:
                # Stop agent
                await self.operations.stop_agent(self.agent_manager.get_agent(agent_id))
                self.status_tracker.update_status(agent_id, AgentStatus.SHUTDOWN)
                
                # Wait for stop to complete
                await asyncio.sleep(1)
                
                # Start agent
                await self.operations.start_agent(self.agent_manager.get_agent(agent_id))
                self.status_tracker.update_status(agent_id, AgentStatus.IDLE)
                
                # Verify agent is healthy
                health_info = self.status_tracker.run_health_check(agent_id)
                if health_info['status'] == 'healthy':
                    return True
                    
                # If not healthy, wait and retry
                retry_count += 1
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    
            except Exception as e:
                logger.error(f"Restart attempt {retry_count + 1} failed for agent {agent_id}: {str(e)}")
                retry_count += 1
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                    
            # Check timeout
            if (datetime.now() - start_time).total_seconds() > self.recovery_timeout:
                logger.error(f"Restart timeout for agent {agent_id}")
                return False
                
        return False
        
    def get_restart_history(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get restart history for an agent.
        
        Args:
            agent_id: The ID of the agent
            
        Returns:
            List[Dict[str, Any]]: List of restart records
        """
        return self._restart_history.get(agent_id, [])
        
    def clear_restart_history(self, agent_id: str) -> None:
        """Clear restart history for an agent.
        
        Args:
            agent_id: The ID of the agent
        """
        if agent_id in self._restart_history:
            self._restart_history[agent_id] = [] 