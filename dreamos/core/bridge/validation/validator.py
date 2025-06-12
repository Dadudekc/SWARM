"""
Bridge Validator
-------------
Validator for bridge messages.
"""

from typing import Any, Dict, Optional, Type
from dataclasses import dataclass
from dreamos.core.shared.validation import BaseValidator, ValidationResult, SchemaValidator
from dreamos.core.utils.metrics import metrics, logger, log_operation
from dreamos.core.utils.exceptions import handle_error

@dataclass
class BridgeMessage:
    """Bridge message data class."""
    type: str
    content: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class BridgeValidator(BaseValidator[BridgeMessage]):
    """Validator for bridge messages."""
    
    # Schema for bridge messages
    MESSAGE_SCHEMA = {
        "type": "object",
        "required": ["type", "content"],
        "properties": {
            "type": {
                "type": "string",
                "pattern": "^[A-Z_]+$"
            },
            "content": {
                "type": "object"
            },
            "metadata": {
                "type": "object",
                "required": False
            }
        }
    }
    
    def __init__(self):
        """Initialize bridge validator."""
        super().__init__("bridge_validator")
        self.schema_validator = SchemaValidator(
            "bridge_schema",
            self.MESSAGE_SCHEMA,
            BridgeMessage
        )
    
    def validate(self, data: Any) -> ValidationResult[BridgeMessage]:
        """Validate bridge message.
        
        Args:
            data: Message data to validate
            
        Returns:
            ValidationResult containing validation status and any errors
        """
        # First validate against schema
        schema_result = self.schema_validator.validate(data)
        if not schema_result.is_valid:
            return schema_result
        
        # Additional bridge-specific validation
        message = schema_result.data
        errors = []
        
        # Validate message type
        if not self._is_valid_message_type(message.type):
            errors.append(self.add_error(
                f"Invalid message type: {message.type}",
                "INVALID_MESSAGE_TYPE",
                {"type": message.type}
            ))
        
        # Validate content based on message type
        content_errors = self._validate_content(message.type, message.content)
        errors.extend(content_errors)
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors)
        
        return ValidationResult(is_valid=True, data=message)
    
    def _is_valid_message_type(self, message_type: str) -> bool:
        """Check if message type is valid.
        
        Args:
            message_type: Message type to check
            
        Returns:
            True if valid, False otherwise
        """
        valid_types = {
            'FILE_CREATED',
            'FILE_MODIFIED',
            'FILE_DELETED',
            'FILE_RENAMED',
            'DIRECTORY_CREATED',
            'DIRECTORY_DELETED',
            'SYSTEM_EVENT',
            'COMMAND',
            'RESPONSE',
            'ERROR'
        }
        return message_type in valid_types
    
    def _validate_content(
        self,
        message_type: str,
        content: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate message content based on type.
        
        Args:
            message_type: Type of message
            content: Message content to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # File event validation
        if message_type in {'FILE_CREATED', 'FILE_MODIFIED', 'FILE_DELETED', 'FILE_RENAMED'}:
            if 'path' not in content:
                errors.append(self.add_error(
                    "Missing required field 'path' for file event",
                    "MISSING_PATH",
                    {"type": message_type}
                ))
            elif not isinstance(content['path'], str):
                errors.append(self.add_error(
                    "Field 'path' must be a string",
                    "INVALID_PATH_TYPE",
                    {"type": message_type, "path": content['path']}
                ))
        
        # Directory event validation
        elif message_type in {'DIRECTORY_CREATED', 'DIRECTORY_DELETED'}:
            if 'path' not in content:
                errors.append(self.add_error(
                    "Missing required field 'path' for directory event",
                    "MISSING_PATH",
                    {"type": message_type}
                ))
            elif not isinstance(content['path'], str):
                errors.append(self.add_error(
                    "Field 'path' must be a string",
                    "INVALID_PATH_TYPE",
                    {"type": message_type, "path": content['path']}
                ))
        
        # Command validation
        elif message_type == 'COMMAND':
            if 'command' not in content:
                errors.append(self.add_error(
                    "Missing required field 'command'",
                    "MISSING_COMMAND",
                    {"type": message_type}
                ))
            elif not isinstance(content['command'], str):
                errors.append(self.add_error(
                    "Field 'command' must be a string",
                    "INVALID_COMMAND_TYPE",
                    {"type": message_type, "command": content['command']}
                ))
        
        # Response validation
        elif message_type == 'RESPONSE':
            if 'status' not in content:
                errors.append(self.add_error(
                    "Missing required field 'status'",
                    "MISSING_STATUS",
                    {"type": message_type}
                ))
            elif not isinstance(content['status'], str):
                errors.append(self.add_error(
                    "Field 'status' must be a string",
                    "INVALID_STATUS_TYPE",
                    {"type": message_type, "status": content['status']}
                ))
        
        # Error validation
        elif message_type == 'ERROR':
            if 'error' not in content:
                errors.append(self.add_error(
                    "Missing required field 'error'",
                    "MISSING_ERROR",
                    {"type": message_type}
                ))
            elif not isinstance(content['error'], str):
                errors.append(self.add_error(
                    "Field 'error' must be a string",
                    "INVALID_ERROR_TYPE",
                    {"type": message_type, "error": content['error']}
                ))
        
        return errors 