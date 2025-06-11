"""
Processor Factory Implementation
-----------------------------
Factory for creating processor instances.
"""

from typing import Dict, Any, Optional, Type, List
import logging
from .base import BaseProcessor
from .message import MessageProcessor
from .response import ResponseProcessor

logger = logging.getLogger(__name__)

class ProcessorFactory:
    """Factory for creating processor instances."""
    
    _processors: Dict[str, Type[BaseProcessor]] = {
        'message': MessageProcessor,
        'response': ResponseProcessor
    }
    
    @classmethod
    def register_processor(cls, name: str, processor_class: Type[BaseProcessor]) -> None:
        """Register a new processor type.
        
        Args:
            name: Name of the processor type
            processor_class: Processor class to register
        """
        if not issubclass(processor_class, BaseProcessor):
            raise ValueError(f"Processor class must inherit from BaseProcessor")
            
        cls._processors[name] = processor_class
        logger.info(f"Registered processor: {name}")
        
    @classmethod
    def create(cls, processor_type: str, config: Optional[Dict[str, Any]] = None) -> BaseProcessor:
        """Create a processor instance.
        
        Args:
            processor_type: Type of processor to create
            config: Optional configuration dictionary
            
        Returns:
            Processor instance
            
        Raises:
            ValueError: If processor type is not registered
        """
        if processor_type not in cls._processors:
            raise ValueError(f"Unknown processor type: {processor_type}")
            
        processor_class = cls._processors[processor_type]
        return processor_class(config)
        
    @classmethod
    def get_available_processors(cls) -> List[str]:
        """Get list of available processor types.
        
        Returns:
            List of processor type names
        """
        return list(cls._processors.keys()) 