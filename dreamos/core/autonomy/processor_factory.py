"""
Response Processor Factory
------------------------
Factory for creating response processors based on mode and configuration.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum, auto

from dreamos.core.autonomy.base.response_loop_daemon import ResponseProcessor
from dreamos.core.autonomy.core_response_processor import CoreResponseProcessor
from bridge.bridge_response_processor import BridgeResponseProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessorMode(Enum):
    """Processor operation modes."""
    CORE = auto()
    BRIDGE = auto()

class ResponseProcessorFactory:
    """Factory for creating response processors."""
    
    def __init__(self, config: Dict[str, Any], discord_client=None):
        """Initialize the factory.
        
        Args:
            config: Configuration dictionary
            discord_client: Optional Discord client for notifications
        """
        self.config = config
        self.discord_client = discord_client
    
    def create(self, mode: ProcessorMode) -> ResponseProcessor:
        """Create a response processor.
        
        Args:
            mode: Processor operation mode
            
        Returns:
            ResponseProcessor instance
        """
        try:
            if mode == ProcessorMode.CORE:
                return CoreResponseProcessor(self.discord_client)
            elif mode == ProcessorMode.BRIDGE:
                return BridgeResponseProcessor(self.config, self.discord_client)
            else:
                raise ValueError(f"Invalid processor mode: {mode}")
                
        except Exception as e:
            logger.error(f"Error creating processor: {e}")
            raise 