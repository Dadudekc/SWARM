"""
Core Response Processor
---------------------
Processes responses for the core response loop.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .validation_engine import ValidationEngine
from dreamos.core.autonomy.base.response_loop_daemon import ResponseProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreResponseProcessor(ResponseProcessor):
    """Processes responses for the core response loop."""
    
    def __init__(self, discord_client=None):
        """Initialize the processor.
        
        Args:
            discord_client: Optional Discord client for notifications
        """
        self.validator = ValidationEngine(discord_client)
    
    async def process_response(self, response: Dict[str, Any], agent_id: str) -> Tuple[bool, Optional[str]]:
        """Process a response.
        
        Args:
            response: Response data
            agent_id: Agent ID
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Extract response info
            test_id = response.get("test_id")
            patch_content = response.get("patch_content")
            
            if not all([test_id, patch_content]):
                return False, "Invalid response format"
            
            # Generate patch ID
            patch_id = f"{test_id}_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Validate patch
            is_valid, validation_result = await self.validator.validate_patch(
                patch_id,
                patch_content,
                test_id,
                agent_id
            )
            
            if not is_valid:
                return False, f"Patch validation failed: {validation_result.get('errors', ['Validation failed'])}"
            
            # Apply patch
            success, error = await self.validator.apply_patch(patch_id, test_id)
            
            if not success:
                return False, f"Patch application failed: {error}"
            
            # Verify patch
            success, error = await self.validator.verify_patch(patch_id, test_id)
            
            if not success:
                await self.validator.rollback_patch(patch_id, test_id)
                return False, f"Patch verification failed: {error}"
            
            return True, None
            
        except Exception as e:
            return False, str(e) 