"""
Bridge Response Processor
---------------------
Unified implementation of the bridge response processor.
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

__all__ = ['ResponseProcessor', 'BridgeResponseProcessor']

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseProcessor:
    """Base class for response processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    async def process(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a response.
        
        Args:
            content: Response content
            metadata: Optional metadata
            
        Returns:
            Processed response
        """
        raise NotImplementedError("Subclasses must implement process()")
        
    async def validate(self, content: str) -> bool:
        """Validate a response.
        
        Args:
            content: Response content
            
        Returns:
            True if valid, False otherwise
        """
        raise NotImplementedError("Subclasses must implement validate()")

class BridgeResponseProcessor(BaseProcessor):
    """Unified bridge response processor."""
    
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
        """Process a response.
        
        Args:
            content: Response content
            metadata: Optional metadata
            
        Returns:
            Processed response
        """
        try:
            # Validate response
            if not self._validate_response(content):
                raise ValueError("Invalid response format")
                
            # Process response
            processed = await self._process_response(content, metadata)
            
            # Update metrics
            self.metrics.record_success()
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            self.metrics.record_error(str(e))
            raise
            
    async def validate(self, content: str) -> bool:
        """Validate a response.
        
        Args:
            content: Response content
            
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
            logger.error(f"Error validating response: {e}")
            return False
            
    def _validate_response(self, content: str) -> bool:
        """Validate response format.
        
        Args:
            content: Response content
            
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
            logger.error(f"Error validating response format: {e}")
            return False
            
    async def _process_response(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process response content.
        
        Args:
            content: Response content
            metadata: Optional metadata
            
        Returns:
            Processed response
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
            logger.error(f"Error processing response content: {e}")
            raise 