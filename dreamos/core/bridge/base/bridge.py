"""
Base Bridge Implementation
------------------------
Abstract base class for all bridge implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import logging
import uuid
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = 0  # Expected errors, no action needed
    INFO = 1   # Expected errors, may need monitoring
    WARNING = 2  # Unexpected but recoverable errors
    ERROR = 3    # Unexpected and unrecoverable errors
    CRITICAL = 4 # System-level errors requiring immediate attention

class BridgeError(Exception):
    """Base class for bridge errors."""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        """Initialize error.
        
        Args:
            message: Error message
            severity: Error severity
            context: Additional error context
            correlation_id: Correlation ID for tracking
        """
        super().__init__(message)
        self.severity = severity
        self.context = context or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.now()
        
        # Log based on severity
        log_method = getattr(logger, severity.name.lower())
        log_method(
            f"Bridge error: {message}",
            extra={
                "severity": severity.name,
                "correlation_id": self.correlation_id,
                "context": self.context
            }
        )

class BridgeConfig:
    """Configuration for bridge implementations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.retry_config = {
            "max_retries": self.config.get("max_retries", 3),
            "initial_delay": self.config.get("initial_delay", 1.0),
            "max_delay": self.config.get("max_delay", 30.0),
            "backoff_factor": self.config.get("backoff_factor", 2.0)
        }
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value

class BaseBridge(ABC):
    """Base class for all bridge implementations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = BridgeConfig(config)
        self.is_running = False
        self.start_time = datetime.now()
        self._correlation_id = str(uuid.uuid4())
        
    async def _retry_operation(
        self,
        operation: str,
        func: callable,
        *args,
        **kwargs
    ) -> Tuple[Any, Optional[BridgeError]]:
        """Retry an operation with exponential backoff.
        
        Args:
            operation: Operation name for logging
            func: Function to retry
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tuple of (result, error)
        """
        retries = 0
        delay = self.config.retry_config["initial_delay"]
        
        while retries < self.config.retry_config["max_retries"]:
            try:
                result = await func(*args, **kwargs)
                return result, None
                
            except Exception as e:
                retries += 1
                if retries == self.config.retry_config["max_retries"]:
                    return None, BridgeError(
                        f"Operation {operation} failed after {retries} retries: {str(e)}",
                        severity=ErrorSeverity.ERROR,
                        context={"operation": operation, "retries": retries},
                        correlation_id=self._correlation_id
                    )
                
                # Calculate next delay with exponential backoff
                delay = min(
                    delay * self.config.retry_config["backoff_factor"],
                    self.config.retry_config["max_delay"]
                )
                
                # Log retry attempt
                logger.warning(
                    f"Retrying {operation} (attempt {retries}/{self.config.retry_config['max_retries']})",
                    extra={
                        "operation": operation,
                        "retry": retries,
                        "delay": delay,
                        "correlation_id": self._correlation_id
                    }
                )
                
                await asyncio.sleep(delay)
        
        return None, BridgeError(
            f"Operation {operation} failed after max retries",
            severity=ErrorSeverity.ERROR,
            context={"operation": operation},
            correlation_id=self._correlation_id
        )
        
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

__all__ = ['BaseBridge', 'BridgeConfig', 'BridgeError', 'ErrorSeverity'] 