"""
Agent Controller

Manages agent lifecycle and coordination.
"""

import logging
from typing import Dict, Optional, Any
from datetime import datetime
import asyncio
from pathlib import Path
import json

from .ui_automation import UIAutomation
from .task_manager import TaskManager
from .devlog_manager import DevLogManager
from .periodic_restart import AgentManager
from ..messaging.cell_phone import CaptainPhone

logger = logging.getLogger('agent_controller')

class AgentController:
    """Controls agent lifecycle and coordination."""
    
    def __init__(self, ui_automation: UIAutomation, discord_token: str, channel_id: int):
        """Initialize the agent controller.
        
        Args:
            ui_automation: UI automation instance
            discord_token: Discord bot token for devlogs
            channel_id: Discord channel ID for devlogs
        """
        self.ui_automation = ui_automation
        self.task_manager = TaskManager()
        self.devlog_manager = DevLogManager(discord_token, channel_id)
        self.captain_phone = CaptainPhone()
        self.agent_manager = AgentManager(ui_automation, discord_token, channel_id)
        
        # Agent state tracking
        self.active_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        
    async def start(self) -> None:
        """Start the agent controller."""
        await self.agent_manager.start()
        logger.info("Started agent controller")
        
    async def stop(self) -> None:
        """Stop the agent controller."""
        await self.agent_manager.stop()
        logger.info("Stopped agent controller")
        
    def start_agent(self, agent_id: str, config: Dict[str, Any]) -> None:
        """Start an agent.
        
        Args:
            agent_id: ID of agent to start
            config: Agent configuration
        """
        if agent_id in self.active_agents:
            logger.warning(f"Agent {agent_id} already running")
            return
            
        # Store agent config
        self.active_agents[agent_id] = config
        
        # Start agent management
        self.agent_manager.start_agent_management(agent_id)
        
        # Create agent task
        self.agent_tasks[agent_id] = asyncio.create_task(
            self._run_agent(agent_id, config)
        )
        
        logger.info(f"Started agent {agent_id}")
        
    def stop_agent(self, agent_id: str) -> None:
        """Stop an agent.
        
        Args:
            agent_id: ID of agent to stop
        """
        if agent_id not in self.active_agents:
            logger.warning(f"Agent {agent_id} not running")
            return
            
        # Stop agent management
        self.agent_manager.stop_agent_management(agent_id)
        
        # Cancel agent task
        if agent_id in self.agent_tasks:
            self.agent_tasks[agent_id].cancel()
            del self.agent_tasks[agent_id]
            
        # Remove agent state
        del self.active_agents[agent_id]
        
        logger.info(f"Stopped agent {agent_id}")
        
    async def _run_agent(self, agent_id: str, config: Dict[str, Any]) -> None:
        """Run an agent.
        
        Args:
            agent_id: ID of agent to run
            config: Agent configuration
        """
        try:
            # Initialize agent
            await self._initialize_agent(agent_id, config)
            
            # Main agent loop
            while True:
                # Process messages
                await self._process_messages(agent_id)
                
                # Update agent state
                await self._update_agent_state(agent_id)
                
                # Sleep to prevent CPU hogging
                await asyncio.sleep(0.1)
                
        except asyncio.CancelledError:
            logger.info(f"Agent {agent_id} task cancelled")
        except Exception as e:
            logger.error(f"Error running agent {agent_id}: {e}")
            # Log error to devlog
            await self.devlog_manager.add_devlog_entry(
                agent_id,
                "system",
                f"Error running agent: {str(e)}"
            )
        finally:
            # Cleanup
            await self._cleanup_agent(agent_id)
            
    async def _initialize_agent(self, agent_id: str, config: Dict[str, Any]) -> None:
        """Initialize an agent.
        
        Args:
            agent_id: ID of agent to initialize
            config: Agent configuration
        """
        # Create agent directory
        agent_dir = Path(f"agents/{agent_id}")
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Save agent config
        with open(agent_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)
            
        # Initialize UI
        self.ui_automation.initialize_agent(agent_id)
        
        # Log initialization
        await self.devlog_manager.add_devlog_entry(
            agent_id,
            "system",
            "Agent initialized"
        )
        
    async def _process_messages(self, agent_id: str) -> None:
        """Process messages for an agent.
        
        Args:
            agent_id: ID of agent to process messages for
        """
        # Get messages from captain phone
        messages = self.captain_phone.get_messages(agent_id)
        
        for message in messages:
            try:
                # Process message
                await self._handle_message(agent_id, message)
            except Exception as e:
                logger.error(f"Error processing message for {agent_id}: {e}")
                # Log error to devlog
                await self.devlog_manager.add_devlog_entry(
                    agent_id,
                    "system",
                    f"Error processing message: {str(e)}"
                )
                
    async def _handle_message(self, agent_id: str, message: Dict[str, Any]) -> None:
        """Handle a message for an agent.
        
        Args:
            agent_id: ID of agent to handle message for
            message: Message to handle
        """
        # Update task context
        self.task_manager.update_task_context(agent_id, message)
        
        # Log message to devlog
        await self.devlog_manager.add_devlog_entry(
            agent_id,
            "message",
            f"Received message: {message['content']}"
        )
        
    async def _update_agent_state(self, agent_id: str) -> None:
        """Update agent state.
        
        Args:
            agent_id: ID of agent to update state for
        """
        # Get task summary
        task_summary = self.task_manager.generate_task_summary(agent_id)
        
        # Update agent state
        self.active_agents[agent_id]["task_summary"] = task_summary
        
        # Log state update to devlog
        await self.devlog_manager.add_devlog_entry(
            agent_id,
            "system",
            f"Updated agent state: {task_summary}"
        )
        
    async def _cleanup_agent(self, agent_id: str) -> None:
        """Clean up an agent.
        
        Args:
            agent_id: ID of agent to clean up
        """
        # Clean up UI
        self.ui_automation.cleanup_agent(agent_id)
        
        # Log cleanup to devlog
        await self.devlog_manager.add_devlog_entry(
            agent_id,
            "system",
            "Agent cleaned up"
        )

    def resume_agent(self, agent_id: str):
        """Resume agent operations
        
        Args:
            agent_id: ID of agent to resume
        """
        try:
            logger.debug(f"Resuming agent: {agent_id}")
            self.current_agent = agent_id
            self.status_updated.emit(f"Resuming agent: {agent_id}")
            
            # Start resume checks for all agents
            self.resume_manager.start_resume_checks(agent_id)
            logger.info(f"Started resume checks for {agent_id}")
                
        except Exception as e:
            logger.error(f"Error resuming agent: {e}")
            self.ui_automation.handle_error(f"Error resuming {agent_id}: {str(e)}")
            
    def verify_agent(self, agent_id: str):
        """Verify agent status
        
        Args:
            agent_id: ID of agent to verify
        """
        try:
            logger.debug(f"Verifying agent: {agent_id}")
            self.status_updated.emit(f"Verifying agent: {agent_id}")
            
            # Ensure resume checks are running
            if agent_id not in self.resume_manager.resume_timers:
                self.resume_manager.start_resume_checks(agent_id)
                logger.info(f"Started resume checks for {agent_id}")
                
        except Exception as e:
            logger.error(f"Error verifying agent: {e}")
            self.ui_automation.handle_error(f"Error verifying {agent_id}: {str(e)}")
            
    def cleanup_agent(self, agent_id: str):
        """Clean up agent resources
        
        Args:
            agent_id: ID of agent to clean up
        """
        try:
            logger.debug(f"Cleaning up agent: {agent_id}")
            self.status_updated.emit(f"Cleaning up agent: {agent_id}")
            
            # Stop resume checks
            self.resume_manager.stop_resume_checks(agent_id)
            logger.info(f"Stopped resume checks for {agent_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up agent: {e}")
            self.ui_automation.handle_error(f"Error cleaning up {agent_id}: {str(e)}")
            
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed status for an agent.
        
        Args:
            agent_id: ID of agent to get status for
            
        Returns:
            Dict containing agent status information
        """
        status = {
            "agent_id": agent_id,
            "is_current": agent_id == self.current_agent,
            "last_resume": None
        }
        
        if agent_id == "Agent-3":
            status.update({
                "periodic_restart_enabled": agent_id in self.restart_manager.restart_timers,
                "last_restart": self.restart_manager.last_restart.get(agent_id)
            })
            
        return status 