"""
Agent Onboarder Module

Handles initial agent setup and onboarding process.
"""

import asyncio
import json
import logging
from typing import Dict, Optional, Any, Union
from pathlib import Path

from ..utils.agent_status import AgentStatus
from .agent_operations import AgentOperations
from .agent_cellphone import AgentCellphone

logger = logging.getLogger(__name__)

class AgentOnboarder:
    """Handles agent onboarding and initial setup."""
    
    def __init__(self,
                 agent_ops: AgentOperations,
                 agent_status: AgentStatus,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the onboarder.
        
        Args:
            agent_ops: Agent operations instance
            agent_status: Agent status instance
            config: Optional configuration dictionary
        """
        self.agent_ops = agent_ops
        self.agent_status = agent_status
        self.config = config or {}
        self.onboarding_steps: Dict = {}
        self._load_config()
        
    def _load_config(self):
        """Load onboarding configuration."""
        try:
            if isinstance(self.config, (str, Path)):
                with open(self.config, 'r') as f:
                    self.onboarding_steps = json.load(f)
            elif isinstance(self.config, dict):
                self.onboarding_steps = self.config
            else:
                raise ValueError(f"Invalid config type: {type(self.config)}")
        except Exception as e:
            logger.error(f"Error loading onboarding config: {e}")
            # Set default steps
            self.onboarding_steps = {
                "steps": [
                    {
                        "name": "initial_greeting",
                        "prompt": "Welcome to Dream.OS! I am your onboarding assistant.",
                        "timeout": 30
                    },
                    {
                        "name": "capability_check",
                        "prompt": "Please confirm your core capabilities are operational.",
                        "timeout": 60
                    },
                    {
                        "name": "integration_test",
                        "prompt": "Testing integration with other agents...",
                        "timeout": 45
                    }
                ]
            }
            
    async def initialize(self) -> bool:
        """Initialize the onboarder.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            # Create onboarding directory if it doesn't exist
            onboarding_dir = Path("runtime/onboarding")
            onboarding_dir.mkdir(parents=True, exist_ok=True)
            
            # Create status file if it doesn't exist
            status_file = onboarding_dir / "onboarding_status.json"
            if not status_file.exists():
                with open(status_file, 'w') as f:
                    json.dump({}, f)
                    
            return True
        except Exception as e:
            logger.error(f"Error initializing onboarder: {e}")
            return False
            
    async def start(self) -> bool:
        """Start the onboarder.
        
        Returns:
            bool: True if start successful
        """
        try:
            # No active tasks to start
            return True
        except Exception as e:
            logger.error(f"Error starting onboarder: {e}")
            return False
            
    async def stop(self) -> bool:
        """Stop the onboarder.
        
        Returns:
            bool: True if stop successful
        """
        try:
            # No active tasks to stop
            return True
        except Exception as e:
            logger.error(f"Error stopping onboarder: {e}")
            return False
            
    async def resume(self) -> bool:
        """Resume the onboarder.
        
        Returns:
            bool: True if resume successful
        """
        return await self.start()
            
    async def onboard_agent(self, agent_id: str) -> bool:
        """Onboard a new agent.
        
        Args:
            agent_id: ID of agent to onboard
            
        Returns:
            True if onboarding successful, False otherwise
        """
        try:
            logger.info(f"Starting onboarding for agent {agent_id}")
            
            # Initialize agent status
            await self.agent_ops.update_agent_status(
                agent_id,
                "onboarding",
                {"step": 0, "total_steps": len(self.onboarding_steps["steps"])}
            )
            
            # Run through onboarding steps
            for i, step in enumerate(self.onboarding_steps["steps"]):
                # Update status
                await self.agent_ops.update_agent_status(
                    agent_id,
                    "onboarding",
                    {"step": i + 1, "total_steps": len(self.onboarding_steps["steps"])}
                )
                
                # Send step prompt
                success = await self.cell_phone.send_message(
                    agent_id,
                    step["prompt"],
                    priority=5  # Highest priority for onboarding
                )
                
                if not success:
                    logger.error(f"Failed to send onboarding step {i} to {agent_id}")
                    return False
                    
                # Wait for response or timeout
                try:
                    await asyncio.wait_for(
                        self._wait_for_step_completion(agent_id, step["name"]),
                        timeout=step["timeout"]
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Onboarding step {i} timed out for {agent_id}")
                    return False
                    
            # Mark onboarding complete
            await self.agent_ops.update_agent_status(
                agent_id,
                "active",
                {"onboarding_complete": True}
            )
            
            logger.info(f"Successfully onboarded agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error during agent onboarding: {e}")
            return False
            
    async def _wait_for_step_completion(self, agent_id: str, step_name: str):
        """Wait for an onboarding step to complete.
        
        Args:
            agent_id: Agent ID
            step_name: Name of the step to wait for
        """
        while True:
            status = await self.agent_ops.get_agent_status(agent_id)
            if status.get("current_step") == step_name and status.get("step_complete"):
                return
            await asyncio.sleep(1)
            
    async def get_onboarding_status(self, agent_id: str) -> Dict:
        """Get onboarding status for an agent.
        
        Args:
            agent_id: Agent ID to check
            
        Returns:
            Dict containing onboarding status info
        """
        try:
            status = await self.agent_ops.get_agent_status(agent_id)
            return {
                "status": status.get("status"),
                "current_step": status.get("current_step"),
                "step_number": status.get("step_number"),
                "total_steps": status.get("total_steps"),
                "onboarding_complete": status.get("onboarding_complete", False)
            }
        except Exception as e:
            logger.error(f"Error getting onboarding status: {e}")
            return {} 