"""
Bridge Message Processor
--------------------
Unified implementation of the bridge message processor.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..base.processor import BaseProcessor
from ..chatgpt.bridge import ChatGPTBridge
from ..monitoring.metrics import BridgeMetrics

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageProcessor:
    """Base class for message processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    async def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a message.
        
        Args:
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Processed message
        """
        raise NotImplementedError("Subclasses must implement process()")
        
    async def validate(self, content: str) -> bool:
        """Validate a message.
        
        Args:
            content: Message content
            
        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")

class BridgeMessageProcessor(BaseProcessor):
    """Unified bridge message processor."""
    
    def __init__(
        self,
        bridge: ChatGPTBridge,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the processor.
        
        Args:
            bridge: ChatGPT bridge instance
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.bridge = bridge
        self.metrics = BridgeMetrics()
        
    async def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a message.
        
        Args:
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Processed message
        """
        try:
            # Validate message
            if not self._validate_message(content):
                raise ValueError("Invalid message format")
                
            # Process message
            processed = await self._process_message(content, metadata)
            
            # Update metrics
            self.metrics.record_success()
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.metrics.record_error(str(e))
            raise
            
    async def validate(self, content: str) -> bool:
        """Validate a message.
        
        Args:
            content: Message content
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check basic format
            if not content or not isinstance(content, str):
                return False
                
            # Check JSON format
            try:
                json.loads(content)
            except json.JSONDecodeError:
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            return False
            
    def _validate_message(self, content: str) -> bool:
        """Validate message format.
        
        Args:
            content: Message content
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Parse JSON
            data = json.loads(content)
            
            # Check required fields
            required = ["content", "metadata"]
            if not all(field in data for field in required):
                return False
                
            # Check content type
            if not isinstance(data["content"], str):
                return False
                
            # Check metadata type
            if not isinstance(data["metadata"], dict):
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error validating message format: {e}")
            return False
            
    async def _process_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process message content.
        
        Args:
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Processed message
        """
        try:
            # Parse JSON
            data = json.loads(content)
            
            # Add processing metadata
            data["metadata"]["processed_at"] = datetime.utcnow().isoformat()
            data["metadata"]["processor"] = self.__class__.__name__
            
            # Add custom metadata if provided
            if metadata:
                data["metadata"].update(metadata)
                
            return data
            
        except Exception as e:
            logger.error(f"Error processing message content: {e}")
            raise 