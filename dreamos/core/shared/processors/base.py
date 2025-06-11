"""
Base Processor Implementation
---------------------------
Abstract base class for all processors in the system.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseProcessor(ABC):
    """Base class for all processors in the system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.is_running = False
        self.start_time = datetime.now()
        self.processed_count = 0
        self.error_count = 0
        
    @abstractmethod
    async def process(self, data: Any) -> Any:
        """Process the input data.
        
        Args:
            data: Input data to process
            
        Returns:
            Processed data
        """
        pass
        
    @abstractmethod
    async def validate(self, data: Any) -> bool:
        """Validate the input data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
        
    async def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """Handle processing errors.
        
        Args:
            error: The error that occurred
            context: Additional context about the error
        """
        self.error_count += 1
        logger.error(f"Processor error: {str(error)}", extra=context)
        
    def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics.
        
        Returns:
            Dictionary of metrics
        """
        return {
            'processed_count': self.processed_count,
            'error_count': self.error_count,
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'is_running': self.is_running
        }
        
    async def start(self) -> None:
        """Start the processor."""
        self.is_running = True
        self.start_time = datetime.now()
        logger.info("Processor started")
        
    async def stop(self) -> None:
        """Stop the processor."""
        self.is_running = False
        logger.info("Processor stopped")
        
    def __str__(self) -> str:
        """String representation of the processor."""
        return f"{self.__class__.__name__}(processed={self.processed_count}, errors={self.error_count})" 