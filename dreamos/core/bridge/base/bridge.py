"""
Base Bridge Implementation
------------------------
Abstract base class for all bridge implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

class BaseBridge(ABC):
    """Base class for all bridge implementations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.is_running = False
        self.start_time = datetime.now()
        
    @abstractmethod
    async def start(self) -> None:
        """Start the bridge."""
        pass
        
    @abstractmethod
    async def stop(self) -> None:
        """Stop the bridge."""
        pass
        
    @abstractmethod
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
        pass
        
    @abstractmethod
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
        pass
        
    @abstractmethod
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
        pass
        
    @abstractmethod
    async def get_health(self) -> Dict[str, Any]:
        """Get bridge health status.
        
        Returns:
            Health status dictionary
        """
        pass
        
    @abstractmethod
    async def get_metrics(self) -> Dict[str, Any]:
        """Get bridge metrics.
        
        Returns:
            Metrics dictionary
        """
        pass 