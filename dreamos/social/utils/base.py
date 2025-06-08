"""
Base utilities for social media operations.
"""

import logging

# Configure basic logger
logger = logging.getLogger(__name__)

class BaseUtils:
    """Base utilities for social media operations."""
    
    def __init__(self, config: dict):
        """Initialize the utilities.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.timeout = config.get("timeout", 30)
        self.logger = logger 
