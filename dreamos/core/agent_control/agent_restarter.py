"""
Agent Restarter Module

Monitors agent status and restarts stalled agents by re-injecting onboarding prompts.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Union
from pathlib import Path

from ..utils.agent_status import AgentStatus
from .agent_operations import AgentOperations
from .agent_cellphone import AgentCellphone

logger = logging.getLogger(__name__)

class AgentRestarter:
    """Monitors and restarts stalled agents."""
    
    def __init__(self, 
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the restarter.
        
        Args:
            agent_ops: Agent operations instance
            agent_status: Agent status instance
            config: Optional configuration dictionary
        """
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.config = config or {}
        
        # Load config values with defaults
        self.status_file = self.config.get("status_file", "agent_status.json")
        self.stall_threshold = self.config.get("stall_threshold", 300)  # 5 minutes
        self.max_restart_attempts = self.config.get("max_restart_attempts", 3)
        
        # State tracking
        self.last_check: Dict[str, datetime] = {}
        self.restart_attempts: Dict[str, int] = {}
        self._monitor_task = None
        
    async def initialize(self) -> bool:
        """Initialize the restarter.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Create status file if it doesn't exist
            status_path = Path(self.status_file)
            if not status_path.exists():
                status_path.parent.mkdir(parents=True, exist_ok=True)
                with open(status_path, 'w') as f:
                    json.dump({}, f)
                    
            return True
        except Exception as e:
            logger.error(f"Error initializing restarter: {e}")
            return False
            
    async def start(self) -> bool:
        """Start monitoring agent status.
        
        Returns:
            bool: True if start successful
        """
        try:
            self._monitor_task = asyncio.create_task(self._monitor_agents())
            return True
        except Exception as e:
            logger.error(f"Error starting restarter: {e}")
            return False
            
    async def stop(self) -> bool:
        """Stop monitoring agent status.
        
        Returns:
            bool: True if stop successful
        """
        try:
            if self._monitor_task:
                self._monitor_task.cancel()
                self._monitor_task = None
            return True
        except Exception as e:
            logger.error(f"Error stopping restarter: {e}")
            return False
            
    async def resume(self) -> bool:
        """Resume monitoring agent status.
        
        Returns:
            bool: True if resume successful
        """
        return await self.start()
        
    async def _monitor_agents(self):
        """Monitor agent status in a loop."""
        while True:
            try:
                await self._check_agent_status()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Back off on error
                
    async def _check_agent_status(self):
        """Check status of all agents."""
        try:
            if not os.path.exists(self.status_file):
                logger.warning(f"Status file {self.status_file} not found")
                return
                
            with open(self.status_file, 'r') as f:
                status_data = json.load(f)
                
            current_time = datetime.now()
            
            for agent_id, status in status_data.items():
                # Skip if agent is already being monitored
                if agent_id in self.last_check:
                    continue
                    
                self.last_check[agent_id] = current_time
                
                # Check if agent is stalled
                if self._is_agent_stalled(agent_id, status):
                    await self._handle_stalled_agent(agent_id)
                    
        except Exception as e:
            logger.error(f"Error checking agent status: {e}")
            
    def _is_agent_stalled(self, agent_id: str, status: Dict) -> bool:
        """Check if an agent is stalled.
        
        Args:
            agent_id: Agent ID to check
            status: Current agent status
            
        Returns:
            True if agent is stalled, False otherwise
        """
        try:
            last_active = datetime.fromisoformat(status.get("last_active", ""))
            return (datetime.now() - last_active).total_seconds() > self.stall_threshold
        except Exception:
            return True  # Consider stalled if we can't parse timestamp
            
    async def _handle_stalled_agent(self, agent_id: str):
        """Handle a stalled agent.
        
        Args:
            agent_id: ID of stalled agent
        """
        try:
            # Check restart attempts
            attempts = self.restart_attempts.get(agent_id, 0)
            if attempts >= self.max_restart_attempts:
                logger.error(f"Agent {agent_id} exceeded max restart attempts")
                return
                
            # Increment attempts
            self.restart_attempts[agent_id] = attempts + 1
            
            # Get onboarding prompt
            onboarding_prompt = await self._get_onboarding_prompt(agent_id)
            if not onboarding_prompt:
                logger.error(f"Could not get onboarding prompt for {agent_id}")
                return
                
            # Inject prompt via cellphone
            success = await self.cell_phone.send_message(
                agent_id,
                onboarding_prompt,
                priority=5  # Highest priority
            )
            
            if success:
                logger.info(f"Successfully restarted agent {agent_id}")
                # Reset restart attempts on success
                self.restart_attempts[agent_id] = 0
            else:
                logger.error(f"Failed to restart agent {agent_id}")
                
        except Exception as e:
            logger.error(f"Error handling stalled agent {agent_id}: {e}")
            
    async def _get_onboarding_prompt(self, agent_id: str) -> Optional[str]:
        """Get onboarding prompt for an agent.
        
        Args:
            agent_id: Agent ID to get prompt for
            
        Returns:
            Onboarding prompt string or None if not found
        """
        try:
            # TODO: Implement proper prompt retrieval
            # For now, return a basic prompt
            return f"Agent {agent_id}, please resume operations and acknowledge this message."
        except Exception as e:
            logger.error(f"Error getting onboarding prompt: {e}")
            return None 