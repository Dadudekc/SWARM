"""
Validator module for GPT router.

This module provides validation functionality for code and responses.
"""

import json
import logging
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

class CodexValidator:
    """Validates code and responses from GPT models."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize validator with optional configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
    def validate_response(self, response: str) -> bool:
        """Validate a response from a GPT model.
        
        Args:
            response: The response string to validate
            
        Returns:
            bool: True if response is valid, False otherwise
        """
        try:
            # Basic validation - check if response is non-empty
            if not response or not response.strip():
                logger.warning("Empty response received")
                return False
                
            # Check for JSON blocks if expected
            if self.config.get("require_json", False):
                if "```json" not in response:
                    logger.warning("Response missing required JSON block")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating response: {e}")
            return False
            
    def validate_code(self, code: str) -> bool:
        """Validate code snippets.
        
        Args:
            code: The code string to validate
            
        Returns:
            bool: True if code is valid, False otherwise
        """
        try:
            # Basic validation - check if code is non-empty
            if not code or not code.strip():
                logger.warning("Empty code received")
                return False
                
            # Add more specific code validation as needed
            return True
            
        except Exception as e:
            logger.error(f"Error validating code: {e}")
            return False
            
    def extract_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract JSON data from a response.
        
        Args:
            response: The response string containing JSON
            
        Returns:
            Optional[Dict[str, Any]]: Parsed JSON data or None if not found/invalid
        """
        try:
            # Look for JSON block
            json_pattern = r"""```json(.*?)```"""
            import re
            match = re.search(json_pattern, response, re.DOTALL)
            
            if match:
                json_str = match.group(1).strip()
                return json.loads(json_str)
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return None 