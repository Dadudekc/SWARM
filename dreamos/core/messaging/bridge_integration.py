"""
Bridge Integration Module
-----------------------
Core integration for ChatGPT bridge functionality.
Handles communication between agents and ChatGPT via the bridge system.
"""

import asyncio
import logging
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from .chatgpt_bridge import ChatGPTBridge
from .request_queue import RequestQueue
from .response_tracker import AgentResponseTracker
from ..monitoring.bridge_health import BridgeHealthMonitor
from ..utils.core_utils import with_retry, format_message, parse_message

logger = logging.getLogger(__name__)

class BridgeIntegration:
    """Core integration for ChatGPT bridge functionality.
    
    This class provides a high-level interface for agents to interact with ChatGPT
    through the bridge system. It handles message routing, response tracking,
    and health monitoring.
    
    Attributes:
        bridge: Core ChatGPT bridge instance
        queue: Request queue for managing messages
        health: Health monitoring system
        tracker: Response tracking system
        config: Bridge configuration
    """
    
    def __init__(self, config_path: str = "config/chatgpt_bridge.yaml"):
        """Initialize bridge integration.
        
        Args:
            config_path: Path to bridge configuration file
        """
        self.bridge = ChatGPTBridge(config_path)
        self.queue = RequestQueue(
            queue_file=str(Path("runtime/bridge_inbox/requests.json"))
        )
        self.health = BridgeHealthMonitor(
            status_file=str(Path("runtime/bridge_inbox/health.json")),
            check_interval=30.0
        )
        self.tracker = AgentResponseTracker()
        self.config = self.bridge.config
        
        # Initialize metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0,
            "last_error": None
        }
        
    async def start(self):
        """Start the bridge integration.
        
        Initializes the bridge, starts health monitoring, and begins
        processing requests from the queue.
        """
        try:
            # Initialize bridge
            await self.bridge.initialize()
            
            # Start health monitoring
            self.health.start()
            
            # Start processing requests
            while True:
                if request := self.queue.get_next_request():
                    await self._process_request(request)
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Bridge integration error: {e}")
            self.metrics["last_error"] = str(e)
            raise
            
    async def stop(self):
        """Stop the bridge integration.
        
        Stops health monitoring and cleans up bridge resources.
        """
        try:
            self.health.stop()
            await self.bridge.cleanup()
        except Exception as e:
            logger.error(f"Error stopping bridge: {e}")
            
    @with_retry(max_retries=3, backoff_factor=2)
    async def _process_request(self, request: Dict[str, Any]):
        """Process a single request with retry logic.
        
        Args:
            request: Request dictionary containing agent_id, prompt, and type
        """
        try:
            start_time = time.time()
            self.metrics["total_requests"] += 1
            
            agent_id = request.get("agent_id")
            prompt = request.get("prompt")
            msg_type = request.get("type", "default")
            
            if not agent_id or not prompt:
                logger.warning("Invalid request format")
                return
                
            # Add metadata to prompt
            enhanced_prompt = self._enhance_prompt(prompt, request)
            
            # Send to ChatGPT via bridge
            response = await self.bridge.send_prompt(enhanced_prompt)
            
            # Track response
            self.tracker.track_response(agent_id, response)
            
            # Update metrics
            response_time = time.time() - start_time
            self.metrics["successful_requests"] += 1
            self.metrics["average_response_time"] = (
                (self.metrics["average_response_time"] * (self.metrics["successful_requests"] - 1) +
                 response_time) / self.metrics["successful_requests"]
            )
            
            # Queue response for agent
            self.queue.add_response(agent_id, response)
            
        except Exception as e:
            self.metrics["failed_requests"] += 1
            self.metrics["last_error"] = str(e)
            logger.error(f"Error processing request: {e}")
            raise
            
    def _enhance_prompt(self, prompt: str, request: Dict[str, Any]) -> str:
        """Enhance prompt with metadata.
        
        Args:
            prompt: Original prompt
            request: Request dictionary containing metadata
            
        Returns:
            Enhanced prompt with metadata
        """
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": request.get("agent_id"),
            "request_type": request.get("type", "default"),
            "task_id": request.get("task_id")
        }
        
        return f"[{metadata}] {prompt}"
            
    async def send_to_agent(self, agent_id: str, message: str, msg_type: str = "default"):
        """Send a message to an agent.
        
        Args:
            agent_id: ID of the target agent
            message: Message to send
            msg_type: Type of message (e.g., "plan_request", "debug_trace")
        """
        try:
            await self.bridge.cell_phone.send_message(
                to_agent=agent_id,
                content=message,
                mode="SYSTEM",
                from_agent="chatgpt_bridge",
                metadata={
                    "tags": ["bridge_response"],
                    "type": msg_type,
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.error(f"Error sending to agent: {e}")
            raise
            
    def get_health_status(self) -> Dict[str, Any]:
        """Get current bridge health status.
        
        Returns:
            Dictionary containing health metrics and status
        """
        status = self.health.get_status()
        status.update({
            "metrics": self.metrics,
            "tracker_status": self.tracker.get_status()
        })
        return status
        
    def get_agent_responses(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get tracked responses for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of tracked responses
        """
        return self.tracker.get_agent_responses(agent_id) 