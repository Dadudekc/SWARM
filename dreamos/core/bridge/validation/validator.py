"""
Bridge Validator
-------------
Validates outbound and inbound messages.
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeValidator:
    """Validates bridge messages and responses."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the validator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.max_content_length = self.config.get("max_content_length", 10000)
        self.max_metadata_size = self.config.get("max_metadata_size", 1000)
        self.required_metadata = self.config.get("required_metadata", ["type", "timestamp"])
        
    def validate_message(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """Validate an outbound message.
        
        Args:
            content: Message content
            metadata: Optional metadata
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check content
        if not content:
            errors.append("Content is empty")
        elif len(content) > self.max_content_length:
            errors.append(f"Content exceeds maximum length of {self.max_content_length}")
            
        # Check metadata
        if not metadata:
            errors.append("Metadata is missing")
        else:
            # Check required fields
            for field in self.required_metadata:
                if field not in metadata:
                    errors.append(f"Required metadata field '{field}' is missing")
                    
            # Check metadata size
            metadata_size = len(json.dumps(metadata))
            if metadata_size > self.max_metadata_size:
                errors.append(f"Metadata exceeds maximum size of {self.max_metadata_size}")
                
            # Validate timestamp
            if "timestamp" in metadata:
                try:
                    datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00"))
                except ValueError:
                    errors.append("Invalid timestamp format")
                    
            # Validate type
            if "type" in metadata:
                if not isinstance(metadata["type"], str):
                    errors.append("Type must be a string")
                elif not re.match(r"^[a-zA-Z0-9_]+$", metadata["type"]):
                    errors.append("Type must contain only alphanumeric characters and underscores")
                    
        return len(errors) == 0, errors
        
    def validate_response(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """Validate an inbound response.
        
        Args:
            content: Response content
            metadata: Optional metadata
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check content
        if not content:
            errors.append("Content is empty")
        elif len(content) > self.max_content_length:
            errors.append(f"Content exceeds maximum length of {self.max_content_length}")
            
        # Check metadata
        if not metadata:
            errors.append("Metadata is missing")
        else:
            # Check required fields
            for field in self.required_metadata:
                if field not in metadata:
                    errors.append(f"Required metadata field '{field}' is missing")
                    
            # Check metadata size
            metadata_size = len(json.dumps(metadata))
            if metadata_size > self.max_metadata_size:
                errors.append(f"Metadata exceeds maximum size of {self.max_metadata_size}")
                
            # Validate timestamp
            if "timestamp" in metadata:
                try:
                    datetime.fromisoformat(metadata["timestamp"].replace("Z", "+00:00"))
                except ValueError:
                    errors.append("Invalid timestamp format")
                    
            # Validate type
            if "type" in metadata:
                if not isinstance(metadata["type"], str):
                    errors.append("Type must be a string")
                elif not re.match(r"^[a-zA-Z0-9_]+$", metadata["type"]):
                    errors.append("Type must contain only alphanumeric characters and underscores")
                    
            # Validate status
            if "status" in metadata:
                if not isinstance(metadata["status"], str):
                    errors.append("Status must be a string")
                elif metadata["status"] not in ["success", "error"]:
                    errors.append("Status must be either 'success' or 'error'")
                    
            # Validate error message if status is error
            if metadata.get("status") == "error" and "error" not in metadata:
                errors.append("Error message is required when status is 'error'")
                
        return len(errors) == 0, errors
        
    def validate_prompt(self, prompt: str) -> Tuple[bool, List[str]]:
        """Validate a prompt.
        
        Args:
            prompt: Prompt to validate
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        # Check length
        if not prompt:
            errors.append("Prompt is empty")
        elif len(prompt) > self.max_content_length:
            errors.append(f"Prompt exceeds maximum length of {self.max_content_length}")
            
        # Check for common issues
        if prompt.count("{") != prompt.count("}"):
            errors.append("Unmatched curly braces in prompt")
            
        if prompt.count("[") != prompt.count("]"):
            errors.append("Unmatched square brackets in prompt")
            
        if prompt.count("(") != prompt.count(")"):
            errors.append("Unmatched parentheses in prompt")
            
        return len(errors) == 0, errors 