"""
ChatGPT Bridge Implementation
--------------------------
Unified implementation of the ChatGPT bridge with enhanced features.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import aiohttp

from ..base.bridge import BaseBridge
from ..base.processor import BaseProcessor
from .prompt import PromptManager
from ..monitoring.metrics import BridgeMetrics
from ..monitoring.health import BridgeHealth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatGPTBridge(BaseBridge):
    """Unified ChatGPT bridge implementation with enhanced features."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the ChatGPT bridge.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        
        # Initialize components
        self.prompt_manager = PromptManager(config)
        self.metrics = BridgeMetrics()
        self.health = BridgeHealth()
        
        # API configuration
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = config.get("model", "gpt-3.5-turbo")
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 30)
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Set up paths
        self.bridge_outbox = Path(self.config.get("paths", {}).get("bridge_outbox", "data/bridge_outbox"))
        self.bridge_inbox = Path(self.config.get("paths", {}).get("bridge_inbox", "data/bridge_inbox"))
        self.archive_dir = Path(self.config.get("paths", {}).get("archive", "data/archive"))
        self.failed_dir = Path(self.config.get("paths", {}).get("failed", "data/failed"))
        
        # Create directories
        for directory in [self.bridge_outbox, self.bridge_inbox, self.archive_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
            
        # Runtime state
        self.processor: Optional[BaseProcessor] = None
        self._task: Optional[asyncio.Task] = None
        
    async def __aenter__(self):
        """Create aiohttp session."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session."""
        if self._session:
            await self._session.close()
            
    async def start(self) -> None:
        """Start the bridge."""
        if self.is_running:
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._run())
        
        logger.info(
            platform="chatgpt_bridge",
            status="started",
            message="ChatGPT bridge started",
            tags=["init", "bridge"]
        )
        
    async def stop(self) -> None:
        """Stop the bridge."""
        if not self.is_running:
            return
            
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        if self._session:
            await self._session.close()
                
        logger.info(
            platform="chatgpt_bridge",
            status="stopped",
            message="ChatGPT bridge stopped",
            tags=["shutdown", "bridge"]
        )
        
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Send a chat request to ChatGPT.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            
        Returns:
            Dict containing the response
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        for attempt in range(self.max_retries):
            try:
                async with self._session.post(
                    self.api_url,
                    headers=headers,
                    json=data,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        if stream:
                            return response
                        return await response.json()
                    else:
                        error = await response.text()
                        raise Exception(f"API error: {error}")
                        
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(1)
                
    async def send_message(
        self,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send a message through the bridge.
        
        Args:
            message: Message to send
            metadata: Optional metadata
            
        Returns:
            Response dictionary
        """
        try:
            # Generate prompt
            prompt = await self.prompt_manager.generate_prompt(message, metadata)
            
            # Format messages
            messages = [
                self.format_system_message(prompt.get("system", "")),
                self.format_user_message(message)
            ]
            
            # Send to ChatGPT
            response = await self.chat(messages)
            
            # Validate response
            if not await self.validate_response(response):
                raise ValueError("Invalid response from ChatGPT")
                
            # Update metrics
            self.metrics.record_success()
            
            return response
            
        except Exception as e:
            self.metrics.record_error(str(e))
            raise
            
    async def receive_message(
        self,
        timeout: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """Receive a message from the bridge.
        
        Args:
            timeout: Optional timeout in seconds
            
        Returns:
            Message dictionary or None if timeout
        """
        try:
            # Check inbox
            for file_path in self.bridge_inbox.glob("*.json"):
                try:
                    with open(file_path) as f:
                        message = json.load(f)
                        
                    # Archive file
                    archive_path = self.archive_dir / file_path.name
                    file_path.rename(archive_path)
                    
                    return message
                    
                except Exception as e:
                    logger.error(f"Error reading {file_path}: {e}")
                    failed_path = self.failed_dir / file_path.name
                    file_path.rename(failed_path)
                    
            return None
            
        except Exception as e:
            self.metrics.record_error(str(e))
            raise
            
    async def validate_response(
        self,
        response: Dict[str, Any]
    ) -> bool:
        """Validate a response.
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not response or "content" not in response:
            return False
            
        if "error" in response:
            return False
            
        return True
        
    async def get_health(self) -> Dict[str, Any]:
        """Get bridge health status.
        
        Returns:
            Health status dictionary
        """
        return {
            "status": "healthy" if self.is_running else "stopped",
            "uptime": (datetime.now() - self.start_time).total_seconds(),
            "metrics": await self.get_metrics()
        }
        
    async def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics.
        
        Returns:
            Metrics dictionary
        """
        return self.metrics.get_metrics()
        
    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """Format a message for the API.
        
        Args:
            role: Message role (system, user, assistant)
            content: Message content
            
        Returns:
            Formatted message dictionary
        """
        return {
            "role": role,
            "content": content
        }
    
    def format_system_message(self, content: str) -> Dict[str, str]:
        """Format a system message.
        
        Args:
            content: System message content
            
        Returns:
            Formatted system message
        """
        return self.format_message("system", content)
    
    def format_user_message(self, content: str) -> Dict[str, str]:
        """Format a user message.
        
        Args:
            content: User message content
            
        Returns:
            Formatted user message
        """
        return self.format_message("user", content)
    
    def format_assistant_message(self, content: str) -> Dict[str, str]:
        """Format an assistant message.
        
        Args:
            content: Assistant message content
            
        Returns:
            Formatted assistant message
        """
        return self.format_message("assistant", content)
        
    async def _run(self) -> None:
        """Main bridge loop."""
        while self.is_running:
            try:
                await self._process_outbox()
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in bridge loop: {e}")
                await asyncio.sleep(5)
                
    async def _process_outbox(self) -> None:
        """Process messages in the outbox."""
        for file_path in self.bridge_outbox.glob("*.json"):
            try:
                with open(file_path) as f:
                    message = json.load(f)
                    
                # Send message
                response = await self.send_message(
                    message["content"],
                    message.get("metadata")
                )
                
                # Archive file
                archive_path = self.archive_dir / file_path.name
                file_path.rename(archive_path)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                failed_path = self.failed_dir / file_path.name
                file_path.rename(failed_path) 