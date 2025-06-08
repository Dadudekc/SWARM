"""
Base handler for Reddit strategy modules.
"""

from typing import Optional, Any, Dict
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    """Abstract base handler for Reddit strategy modules."""
    
    def __init__(self, session: Optional[Any] = None):
        """Initialize base handler.
        
        Args:
            session: Optional session object for API interactions
        """
        self.session = session
        self._config = {}
        
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the handler with settings.
        
        Args:
            config: Configuration dictionary
        """
        self._config = config
        
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
        
    async def handle(self, *args: Any, **kwargs: Any) -> Any:
        """Handle the operation. Must be implemented by subclasses.
        
        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Operation result
            
        Raises:
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Handler must implement handle()")
        
    def validate(self) -> bool:
        """Validate handler state.
        
        Returns:
            bool: True if valid
        """
        return True
        
    def cleanup(self) -> None:
        """Clean up resources."""
        pass 
