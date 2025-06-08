"""
Debug Response Processor

Debug implementation of the response processor.
"""

import logging
from typing import Dict, Any, Optional
from ..base.response_loop_daemon import ResponseProcessor

logger = logging.getLogger(__name__)

class DebugResponseProcessor(ResponseProcessor):
    """Debug response processor implementation."""
    
    def process_response(self, response: Dict[str, Any]) -> bool:
        """Process a response in debug mode.
        
        Args:
            response: Response dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract response data
            agent_id = response.get("agent_id")
            content = response.get("content")
            
            if not agent_id or not content:
                logger.warning("Invalid response format")
                return False
            
            # Log debug info
            logger.info(f"Debug mode: Processing response for {agent_id}")
            logger.debug(f"Response content: {content}")
            logger.debug(f"Full response: {response}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing debug response: {e}")
            return False 