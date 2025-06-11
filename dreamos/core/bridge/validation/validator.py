"""
Bridge Validator
-------------
Validator for bridge messages.
"""

from typing import Dict, Any, Optional
from dreamos.core.shared.validation import BaseValidator, ValidationError
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.utils.json_utils import load_json, save_json

class BridgeValidator(BaseValidator):
    """Validator for bridge messages."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the validator.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.validation_rules = config.get('validation_rules', {})
        
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate bridge message.
        
        Args:
            data: Message to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = self.validation_rules.get('required_fields', ['type', 'content'])
        if not all(field in data for field in required_fields):
            return False
            
        # Check field types
        field_types = self.validation_rules.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False
                
        return True
        
    async def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules.
        
        Returns:
            Validation rules dictionary
        """
        return self.validation_rules 