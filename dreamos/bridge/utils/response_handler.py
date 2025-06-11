"""
Response handling utilities for the bridge.
"""

import json
import logging
import re
from typing import Tuple

logger = logging.getLogger('bridge')

class HybridResponseHandler:
    """Parses hybrid responses containing both text and structured data."""
    
    def parse_hybrid_response(self, raw_response: str) -> Tuple[str, dict]:
        """Extract text and structured JSON data from a hybrid response."""
        logger.info("Parsing hybrid response for narrative text and MEMORY_UPDATE JSON")
        
        # Regex to capture JSON block between ```json and ```
        json_pattern = r"""```json(.*?)```"""
        match = re.search(json_pattern, raw_response, re.DOTALL)

        if match:
            json_content = match.group(1).strip()
            try:
                memory_update = json.loads(json_content)
                logger.info("Successfully parsed MEMORY_UPDATE JSON")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                memory_update = {}
        else:
            logger.info("No JSON block found in the response")
            memory_update = {}

        # Remove the JSON block from the raw response to extract pure narrative text
        text_part = re.sub(json_pattern, "", raw_response, flags=re.DOTALL).strip()

        return text_part, memory_update

def parse_hybrid_response(raw_response: str) -> Tuple[str, dict]:
    """Extract text and structured JSON data from a hybrid response.
    
    Args:
        raw_response: The raw response string containing both text and JSON
        
    Returns:
        Tuple of (text_part, memory_update) where:
        - text_part is the narrative text with JSON blocks removed
        - memory_update is the parsed JSON data or empty dict if none found
    """
    handler = HybridResponseHandler()
    return handler.parse_hybrid_response(raw_response) 