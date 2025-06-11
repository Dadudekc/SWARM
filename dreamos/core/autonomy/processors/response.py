"""
Autonomy Response Processor
-------------------------
Processes and validates responses in the autonomy system.
"""

from typing import Dict, Any, Optional
import logging
from dreamos.core.shared.processors.response import ResponseProcessor

logger = logging.getLogger(__name__)

class AutonomyResponseProcessor(ResponseProcessor):
    """Processes and validates responses in the autonomy system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the autonomy response processor.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        # Add autonomy-specific required fields
        self.required_fields.extend(['agent_id', 'timestamp'])
        # Add autonomy-specific valid statuses
        self.valid_statuses.extend(['pending', 'in_progress', 'completed'])
        
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate an autonomy response.
        
        Args:
            data: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        # First validate using base processor
        if not await super().validate(data):
            return False
            
        # Additional autonomy-specific validation
        if 'agent_id' in data and not isinstance(data['agent_id'], str):
            logger.error("agent_id must be a string")
            return False
            
        if 'timestamp' in data and not isinstance(data['timestamp'], str):
            logger.error("timestamp must be a string")
            return False
            
        return True
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process an autonomy response.
        
        Args:
            data: Response to process
            
        Returns:
            Processed response
        """
        # First process using base processor
        processed = await super().process(data)
        
        # Add autonomy-specific processing
        if 'agent_id' in processed:
            processed['agent_id'] = processed['agent_id'].strip()
            
        if 'timestamp' in processed:
            # Ensure timestamp is in ISO format
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(processed['timestamp'])
                processed['timestamp'] = dt.isoformat()
            except ValueError:
                logger.error(f"Invalid timestamp format: {processed['timestamp']}")
                processed['timestamp'] = datetime.now().isoformat()
                
        return processed 