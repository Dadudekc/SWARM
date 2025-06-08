"""
High Priority Dispatcher Module

Handles prompt bouncing and high-priority message routing between agents.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

from ..utils.message_processor import MessageProcessor
from ..utils.agent_status import AgentStatus
from .agent_operations import AgentOperations

logger = logging.getLogger(__name__)

class HighPriorityDispatcher:
    """Handles high-priority message routing and prompt bouncing between agents."""
    
    def __init__(self, message_processor: MessageProcessor, agent_ops: AgentOperations):
        """Initialize the dispatcher.
        
        Args:
            message_processor: Message processor instance
            agent_ops: Agent operations instance
        """
        self.message_processor = message_processor
        self.agent_ops = agent_ops
        self.bounce_queue: List[Dict] = []
        self.last_bounce_time: Dict[str, datetime] = {}
        self.min_bounce_interval = timedelta(seconds=30)
        
    async def bounce_prompt(self, 
                          source_agent: str,
                          target_agents: Union[str, List[str]],
                          prompt: str,
                          priority: int = 1) -> bool:
        """Bounce a prompt between agents.
        
        Args:
            source_agent: ID of the source agent
            target_agents: Single target agent ID or list of target agent IDs
            prompt: The prompt to bounce
            priority: Priority level (1-5, 5 being highest)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert single target to list
            if isinstance(target_agents, str):
                target_agents = [target_agents]
                
            # Check bounce cooldown
            current_time = datetime.now()
            for agent in target_agents:
                last_bounce = self.last_bounce_time.get(agent)
                if last_bounce and (current_time - last_bounce) < self.min_bounce_interval:
                    logger.warning(f"Bounce cooldown active for agent {agent}")
                    continue
                    
                # Create bounce message
                message = {
                    "type": "BOUNCE",
                    "source": source_agent,
                    "target": agent,
                    "prompt": prompt,
                    "priority": priority,
                    "timestamp": current_time.isoformat()
                }
                
                # Add to bounce queue
                self.bounce_queue.append(message)
                self.last_bounce_time[agent] = current_time
                
            # Process queue
            await self._process_bounce_queue()
            return True
            
        except Exception as e:
            logger.error(f"Error bouncing prompt: {e}")
            return False
            
    async def _process_bounce_queue(self):
        """Process the bounce message queue."""
        while self.bounce_queue:
            message = self.bounce_queue.pop(0)
            
            try:
                # Send via message processor
                await self.message_processor.send_message(message)
                
                # Update agent status
                await self.agent_ops.update_agent_status(
                    message["target"],
                    "processing_bounce",
                    {"source": message["source"], "priority": message["priority"]}
                )
                
            except Exception as e:
                logger.error(f"Error processing bounce message: {e}")
                # Requeue failed message
                self.bounce_queue.append(message)
                await asyncio.sleep(1)  # Prevent tight loop
                
    async def get_bounce_status(self, agent_id: str) -> Dict:
        """Get bounce status for an agent.
        
        Args:
            agent_id: Agent ID to check
            
        Returns:
            Dict containing bounce status info
        """
        try:
            last_bounce = self.last_bounce_time.get(agent_id)
            return {
                "last_bounce": last_bounce.isoformat() if last_bounce else None,
                "queue_position": next(
                    (i for i, msg in enumerate(self.bounce_queue) 
                     if msg["target"] == agent_id),
                    None
                ),
                "cooldown_active": (
                    last_bounce and 
                    (datetime.now() - last_bounce) < self.min_bounce_interval
                )
            }
        except Exception as e:
            logger.error(f"Error getting bounce status: {e}")
            return {} 