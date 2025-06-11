"""
Base Controller Module

Provides the foundation for all Dream.OS controllers, implementing shared functionality
and defining the interface that all controllers must implement.
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from dreamos.core.utils.agent_status import AgentStatus
from dreamos.core.utils.message_processor import MessageProcessor

logger = logging.getLogger(__name__)

class BaseController(ABC):
    """Base class for all Dream.OS controllers."""
    
    def __init__(self, 
                 message_processor: MessageProcessor,
                 agent_status: AgentStatus,
                 config: Optional[Dict[str, Any]] = None):
        """Initialize the base controller.
        
        Args:
            message_processor: For handling message routing
            agent_status: For tracking agent state
            config: Optional configuration dictionary
        """
        self.message_processor = message_processor
        self.agent_status = agent_status
        self.config = config or {}
        self._initialized = False
        self._running = False
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the controller.
        
        Returns:
            bool: True if initialization successful
        """
        pass
        
    @abstractmethod
    async def start(self) -> bool:
        """Start the controller.
        
        Returns:
            bool: True if start successful
        """
        pass
        
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the controller.
        
        Returns:
            bool: True if stop successful
        """
        pass
        
    @abstractmethod
    async def resume(self) -> bool:
        """Resume the controller after a pause.
        
        Returns:
            bool: True if resume successful
        """
        pass
        
    @property
    def is_initialized(self) -> bool:
        """Check if controller is initialized."""
        return self._initialized
        
    @property
    def is_running(self) -> bool:
        """Check if controller is running."""
        return self._running
        
    async def handle_error(self, error: Exception) -> None:
        """Handle controller errors.
        
        Args:
            error: The exception that occurred
        """
        logger.error(f"Controller error: {error}")
        # Default error handling - can be overridden by subclasses
        await self.stop()
        
    async def update_status(self, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Update controller status.
        
        Args:
            status: New status string
            details: Optional status details
        """
        await self.agent_status.update_status(
            controller_id=self.__class__.__name__,
            status=status,
            details=details
        )
        
    async def send_message(self, message: str, priority: int = 0) -> None:
        """Send a message through the message processor.
        
        Args:
            message: Message to send
            priority: Message priority (0 = normal)
        """
        await self.message_processor.send_message(
            message=message,
            priority=priority,
            source=self.__class__.__name__
        )
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)
        
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value 