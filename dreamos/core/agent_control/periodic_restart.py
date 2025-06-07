"""
Periodic Restart Module

Manages agent periodic restarts and resumption.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger('periodic_restart')

class AgentManager:
    """Manages agent periodic restarts."""
    
    def __init__(self, ui_automation, discord_token: str, channel_id: int):
        """Initialize the agent manager.
        
        Args:
            ui_automation: UI automation instance
            discord_token: Discord bot token for devlogs
            channel_id: Discord channel ID for devlogs
        """
        self.ui_automation = ui_automation
        self.discord_token = discord_token
        self.channel_id = channel_id
        self.agent_restart_tasks: Dict[str, asyncio.Task] = {}
        
    async def start(self) -> None:
        """Start the agent manager."""
        logger.info("Started agent manager")
        
    async def stop(self) -> None:
        """Stop the agent manager."""
        # Cancel all restart tasks
        for task in self.agent_restart_tasks.values():
            task.cancel()
        self.agent_restart_tasks.clear()
        logger.info("Stopped agent manager")
        
    def start_agent_management(self, agent_id: str) -> None:
        """Start managing an agent.
        
        Args:
            agent_id: ID of agent to manage
        """
        if agent_id in self.agent_restart_tasks:
            logger.warning(f"Agent {agent_id} already being managed")
            return
            
        # Create restart task
        self.agent_restart_tasks[agent_id] = asyncio.create_task(
            self._manage_agent(agent_id)
        )
        logger.info(f"Started managing agent {agent_id}")
        
    def stop_agent_management(self, agent_id: str) -> None:
        """Stop managing an agent.
        
        Args:
            agent_id: ID of agent to stop managing
        """
        if agent_id not in self.agent_restart_tasks:
            logger.warning(f"Agent {agent_id} not being managed")
            return
            
        # Cancel restart task
        self.agent_restart_tasks[agent_id].cancel()
        del self.agent_restart_tasks[agent_id]
        logger.info(f"Stopped managing agent {agent_id}")
        
    async def _manage_agent(self, agent_id: str) -> None:
        """Manage an agent's periodic restarts.
        
        Args:
            agent_id: ID of agent to manage
        """
        try:
            while True:
                # Wait for restart interval
                await asyncio.sleep(3600)  # 1 hour
                
                # Restart agent
                await self._restart_agent(agent_id)
                
        except asyncio.CancelledError:
            logger.info(f"Agent {agent_id} management cancelled")
        except Exception as e:
            logger.error(f"Error managing agent {agent_id}: {e}")
            
    async def _restart_agent(self, agent_id: str) -> None:
        """Restart an agent.
        
        Args:
            agent_id: ID of agent to restart
        """
        try:
            # Stop agent
            self.ui_automation.stop_agent(agent_id)
            
            # Wait for stop
            await asyncio.sleep(5)
            
            # Start agent
            self.ui_automation.start_agent(agent_id)
            
            logger.info(f"Restarted agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error restarting agent {agent_id}: {e}")

class AgentResumeManager:
    """Manages agent resumption after restarts."""
    
    def __init__(self, ui_automation):
        """Initialize the agent resume manager.
        
        Args:
            ui_automation: UI automation instance
        """
        self.ui_automation = ui_automation
        self.resume_tasks: Dict[str, asyncio.Task] = {}
        
    async def start(self) -> None:
        """Start the agent resume manager."""
        logger.info("Started agent resume manager")
        
    async def stop(self) -> None:
        """Stop the agent resume manager."""
        # Cancel all resume tasks
        for task in self.resume_tasks.values():
            task.cancel()
        self.resume_tasks.clear()
        logger.info("Stopped agent resume manager")
        
    def start_resume_management(self, agent_id: str) -> None:
        """Start managing an agent's resumption.
        
        Args:
            agent_id: ID of agent to manage
        """
        if agent_id in self.resume_tasks:
            logger.warning(f"Agent {agent_id} already being managed for resumption")
            return
            
        # Create resume task
        self.resume_tasks[agent_id] = asyncio.create_task(
            self._manage_resume(agent_id)
        )
        logger.info(f"Started managing agent {agent_id} resumption")
        
    def stop_resume_management(self, agent_id: str) -> None:
        """Stop managing an agent's resumption.
        
        Args:
            agent_id: ID of agent to stop managing
        """
        if agent_id not in self.resume_tasks:
            logger.warning(f"Agent {agent_id} not being managed for resumption")
            return
            
        # Cancel resume task
        self.resume_tasks[agent_id].cancel()
        del self.resume_tasks[agent_id]
        logger.info(f"Stopped managing agent {agent_id} resumption")
        
    async def _manage_resume(self, agent_id: str) -> None:
        """Manage an agent's resumption.
        
        Args:
            agent_id: ID of agent to manage
        """
        try:
            while True:
                # Check if agent needs resumption
                if self.ui_automation.needs_resume(agent_id):
                    await self._resume_agent(agent_id)
                    
                # Wait before next check
                await asyncio.sleep(60)  # 1 minute
                
        except asyncio.CancelledError:
            logger.info(f"Agent {agent_id} resume management cancelled")
        except Exception as e:
            logger.error(f"Error managing agent {agent_id} resumption: {e}")
            
    async def _resume_agent(self, agent_id: str) -> None:
        """Resume an agent.
        
        Args:
            agent_id: ID of agent to resume
        """
        try:
            # Resume agent
            self.ui_automation.resume_agent(agent_id)
            logger.info(f"Resumed agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}") 