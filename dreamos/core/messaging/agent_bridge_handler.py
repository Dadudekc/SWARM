"""
Agent Bridge Handler
------------------
Base class for agent integration with the ChatGPT bridge.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .bridge_integration import BridgeIntegration
from .utils.core_utils import format_message, parse_message
from ..monitoring.agent_metrics import AgentMetrics

logger = logging.getLogger(__name__)

class AgentBridgeHandler:
    """Base handler for agent integration with ChatGPT bridge."""
    
    def __init__(self, agent_id: str, config_path: str = "config/chatgpt_bridge.yaml"):
        """Initialize bridge handler.
        
        Args:
            agent_id: ID of the agent
            config_path: Path to bridge configuration
        """
        self.agent_id = agent_id
        self.bridge = BridgeIntegration(config_path)
        self.metrics = AgentMetrics(agent_id)
        self._running = False
        
    async def start(self):
        """Start the bridge handler."""
        if self._running:
            return
            
        try:
            await self.bridge.start()
            self._running = True
            self.metrics.record_event("bridge_started")
            logger.info(f"Bridge handler started for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to start bridge handler: {e}")
            raise
            
    async def stop(self):
        """Stop the bridge handler."""
        if not self._running:
            return
            
        try:
            await self.bridge.stop()
            self._running = False
            self.metrics.record_event("bridge_stopped")
            logger.info(f"Bridge handler stopped for agent {self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to stop bridge handler: {e}")
            raise
            
    async def process_with_chatgpt(
        self,
        prompt: str,
        msg_type: str = "default",
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """Process a prompt through ChatGPT with retries.
        
        Args:
            prompt: Prompt to send
            msg_type: Type of message
            max_retries: Maximum number of retries
            
        Returns:
            Response dictionary or None if failed
        """
        if not self._running:
            raise RuntimeError("Bridge handler not started")
            
        start_time = datetime.now()
        
        for attempt in range(max_retries):
            try:
                response = await self.bridge.send_to_agent(
                    agent_id=self.agent_id,
                    message=prompt,
                    msg_type=msg_type
                )
                
                if self._validate_response(response):
                    self._record_success(start_time, msg_type)
                    return response
                    
            except Exception as e:
                self._record_error(e, attempt, max_retries)
                if attempt == max_retries - 1:
                    raise
                    
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
        return None
        
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate ChatGPT response.
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not response or "content" not in response:
            logger.warning(f"Invalid response format: {response}")
            return False
            
        if "error" in response:
            logger.warning(f"Response contains error: {response['error']}")
            return False
            
        return True
        
    def _record_success(self, start_time: datetime, msg_type: str):
        """Record successful bridge interaction.
        
        Args:
            start_time: Start time of interaction
            msg_type: Type of message
        """
        duration = (datetime.now() - start_time).total_seconds()
        self.metrics.record_bridge_success(msg_type, duration)
        
    def _record_error(self, error: Exception, attempt: int, max_retries: int):
        """Record bridge error.
        
        Args:
            error: Error that occurred
            attempt: Current attempt number
            max_retries: Maximum number of retries
        """
        self.metrics.record_bridge_error(str(error), attempt, max_retries)
        logger.error(f"Bridge error (attempt {attempt + 1}/{max_retries}): {error}")
        
    async def check_health(self) -> Dict[str, Any]:
        """Check bridge health status.
        
        Returns:
            Health status dictionary
        """
        if not self._running:
            return {"status": "stopped"}
            
        try:
            status = self.bridge.get_health_status()
            self.metrics.record_health_check(status)
            return status
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "error": str(e)}
            
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics.
        
        Returns:
            Metrics dictionary
        """
        return self.metrics.get_metrics()
        
    async def get_responses(self) -> List[Dict[str, Any]]:
        """Get tracked responses.
        
        Returns:
            List of tracked responses
        """
        return self.bridge.get_agent_responses(self.agent_id) 