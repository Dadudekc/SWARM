"""
Base Processor Interface
--------------------
Defines the interface that all response processors must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class BaseProcessor(ABC):
    """Base class for all response processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the processor.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.start_time = datetime.now()
        self.total_processed = 0
        self.total_failed = 0
        
    @abstractmethod
    async def process(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process a response.
        
        Args:
            response: Response to process
            
        Returns:
            Processed response
        """
        pass
        
    @abstractmethod
    async def validate(self, response: Dict[str, Any]) -> bool:
        """Validate a response.
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
        
    @abstractmethod
    async def handle_error(
        self,
        error: Exception,
        response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle an error.
        
        Args:
            error: Error that occurred
            response: Response that caused error
            
        Returns:
            Error response
        """
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get processor metrics.
        
        Returns:
            Metrics dictionary
        """
        pass
        
    def _update_metrics(self, success: bool) -> None:
        """Update processor metrics.
        
        Args:
            success: Whether processing was successful
        """
        self.total_processed += 1
        if not success:
            self.total_failed += 1 