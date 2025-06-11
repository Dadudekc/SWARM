"""
Message Processor Implementation
-----------------------------
Processes and validates messages in the system.
"""

from typing import Dict, Any, Optional
import logging
from .base import BaseProcessor
from datetime import datetime

logger = logging.getLogger(__name__)

class MessageProcessor(BaseProcessor):
    """Processes and validates messages."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the message processor.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.required_fields = config.get('required_fields', ['type', 'content'])
        self.max_content_length = config.get('max_content_length', 1000)
        
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate a message.
        
        Args:
            data: Message to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(data, dict):
            logger.error("Message must be a dictionary")
            return False
            
        # Check required fields
        for field in self.required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
                
        # Check content length
        if 'content' in data and len(str(data['content'])) > self.max_content_length:
            logger.error(f"Content exceeds maximum length of {self.max_content_length}")
            return False
            
        return True
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a message.
        
        Args:
            data: Message to process
            
        Returns:
            Processed message
        """
        if not await self.validate(data):
            raise ValueError("Invalid message")
            
        try:
            # Add processing timestamp
            processed = data.copy()
            processed['processed_at'] = datetime.now().isoformat()
            
            # Increment processed count
            self.processed_count += 1
            
            return processed
            
        except Exception as e:
            await self.handle_error(e, {'message': data})
            raise 