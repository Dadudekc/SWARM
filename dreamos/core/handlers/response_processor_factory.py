"""
Response Processor Factory
------------------------
Factory for creating response processors based on mode and configuration.
"""

import logging
from typing import Dict, Any, Optional

from dreamos.core.autonomy.base.response_loop_daemon import ResponseProcessor
from dreamos.core.autonomy.processors.core_processor import CoreResponseProcessor
from dreamos.core.autonomy.processors.test_processor import TestResponseProcessor
from dreamos.core.autonomy.processors.debug_processor import DebugResponseProcessor
from dreamos.core.autonomy.processors.production_processor import ProductionResponseProcessor
from dreamos.core.autonomy.processor_mode import ProcessorMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            elif mode == ProcessorMode.TEST:
                return TestResponseProcessor(self.discord_client)
            elif mode == ProcessorMode.DEBUG:
                return DebugResponseProcessor(self.discord_client)
            elif mode == ProcessorMode.PRODUCTION:
                return ProductionResponseProcessor(self.discord_client)
            else:
                raise ValueError(f"Invalid processor mode: {mode}")
                
        except Exception as e:
            logger.error(f"Error creating processor: {e}")
            raise 