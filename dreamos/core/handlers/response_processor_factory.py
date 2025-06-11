"""
Response Processor Factory
------------------------
Factory for creating response processors based on mode.
"""

from typing import Optional
import logging
from dreamos.core.shared.processors import ResponseProcessor, ProcessorFactory
from dreamos.core.shared.processors.mode import ProcessorMode

logger = logging.getLogger(__name__)

class ResponseProcessorFactory:
    """Factory for creating response processors."""
    
    def __init__(self, discord_client=None):
        """Initialize the factory.
        
        Args:
            discord_client: Optional Discord client for message handling
        """
        self.discord_client = discord_client
        self.processor_factory = ProcessorFactory()
        
    def create_processor(self, mode: ProcessorMode) -> ResponseProcessor:
        """Create a response processor for the given mode.
        
        Args:
            mode: Processor mode to create
            
        Returns:
            ResponseProcessor instance
        """
        config = {
            'discord_client': self.discord_client,
            'mode': mode
        }
        
        return self.processor_factory.create('response', config) 