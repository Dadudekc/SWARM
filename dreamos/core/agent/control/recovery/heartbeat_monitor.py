"""
Heartbeat Monitoring Module

Handles monitoring of agent heartbeats and detection of agent failures.
Manages retry counts, cooldown periods, and recovery actions.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Set

from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_status import AgentStatus

logger = logging.getLogger(__name__)

class HeartbeatMonitor:
    """Monitors agent heartbeats and manages recovery."""
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 config: Optional[Dict] = None):
        """Initialize the heartbeat monitor.
        
        Args:
            agent_ops: Agent operations interface
            agent_status: Agent status tracker
            config: Optional configuration dictionary
        """
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.config = config or {}
        
        # Recovery settings
        self.heartbeat_timeout = self.config.get('heartbeat_timeout', 300)  # 5 minutes
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_cooldown = self.config.get('retry_cooldown', 60)  # 1 minute
        self.restart_cooldown = self.config.get('restart_cooldown', 300)  # 5 minutes
        
        # State tracking
        self._retry_counts: Dict[str, int] = {}
        self._last_restart: Dict[str, float] = {}
        self._monitoring = False
        self._monitor_task = None
        self._failed_agents: Set[str] = set()
        
    async def start(self) -> bool:
        """Start heartbeat monitoring.
        
        Returns:
            bool: True if monitoring started successfully
        """
        if self._monitoring:
            return True
            
        try:
            self._monitoring = True
            self._monitor_task = asyncio.create_task(self._monitor_heartbeats())
            return True
            
        except Exception as e:
            logger.error(f"Failed to start heartbeat monitoring: {e}")
            self._monitoring = False
            return False
            
    async def stop(self) -> bool:
        """Stop heartbeat monitoring.
        
        Returns:
            bool: True if monitoring stopped successfully
        """
        if not self._monitoring:
            return True
            
        try:
            self._monitoring = False
            if self._monitor_task:
                self._monitor_task.cancel()
                try:
                    await self._monitor_task
                except asyncio.CancelledError:
                    pass
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop heartbeat monitoring: {e}")
            return False
            
    async def _monitor_heartbeats(self) -> None:
        """Monitor agent heartbeats and handle failures."""
        while self._monitoring:
            try:
                # Get active agents
                active_agents = await self.agent_ops.get_active_agents()
                
                # Check each agent
                for agent_id in active_agents:
                    if await self._check_heartbeat(agent_id):
                        # Agent is healthy
                        self._failed_agents.discard(agent_id)
                    else:
                        # Agent failed
                        self._failed_agents.add(agent_id)
                        await self._handle_agent_failure(agent_id)
                        
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in heartbeat monitoring: {e}")
                await asyncio.sleep(60)  # Wait longer on error
                
    async def _check_heartbeat(self, agent_id: str) -> bool:
        """Check if an agent's heartbeat is healthy.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if heartbeat is healthy
        """
        try:
            # Get last heartbeat time
            last_heartbeat = await self.agent_status.get_last_heartbeat(agent_id)
            if not last_heartbeat:
                return False
                
            # Check if heartbeat is too old
            if datetime.now() - last_heartbeat > timedelta(seconds=self.heartbeat_timeout):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error checking heartbeat for agent {agent_id}: {e}")
            return False
            
    async def _handle_agent_failure(self, agent_id: str) -> None:
        """Handle an agent failure.
        
        Args:
            agent_id: ID of the failed agent
        """
        try:
            # Check if we can restart
            if not self._can_restart(agent_id):
                return
                
            # Increment retry count
            self._retry_counts[agent_id] = self._retry_counts.get(agent_id, 0) + 1
            
            # Log failure
            await self._log_failure(agent_id)
            
            # Attempt recovery
            if self._retry_counts[agent_id] <= self.max_retries:
                await self.agent_ops.restart_agent(agent_id)
                self._last_restart[agent_id] = time.time()
                
        except Exception as e:
            logger.error(f"Error handling failure for agent {agent_id}: {e}")
            
    def _can_restart(self, agent_id: str) -> bool:
        """Check if an agent can be restarted.
        
        Args:
            agent_id: ID of the agent to check
            
        Returns:
            bool: True if agent can be restarted
        """
        # Check retry count
        if self._retry_counts.get(agent_id, 0) >= self.max_retries:
            return False
            
        # Check cooldown
        last_restart = self._last_restart.get(agent_id, 0)
        if time.time() - last_restart < self.restart_cooldown:
            return False
            
        return True
        
    async def _log_failure(self, agent_id: str) -> None:
        """Log an agent failure.
        
        Args:
            agent_id: ID of the failed agent
        """
        try:
            # Get failure info
            retry_count = self._retry_counts.get(agent_id, 0)
            last_heartbeat = await self.agent_status.get_last_heartbeat(agent_id)
            
            # Log failure
            logger.warning(
                f"Agent {agent_id} failed - "
                f"Retry count: {retry_count}, "
                f"Last heartbeat: {last_heartbeat}"
            )
            
        except Exception as e:
            logger.error(f"Error logging failure for agent {agent_id}: {e}")
            
    def get_failed_agents(self) -> Set[str]:
        """Get set of failed agents.
        
        Returns:
            Set[str]: Set of failed agent IDs
        """
        return self._failed_agents.copy() 