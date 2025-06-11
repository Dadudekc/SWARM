"""
Base Validator Interface
--------------------
Defines the interface that all bridge validators must follow.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

class BaseValidator(ABC):
    """Base class for all bridge validators."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the validator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
    @abstractmethod
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
        
    @abstractmethod
    async def handle_error(self, error: Exception, data: Dict[str, Any]) -> None:
        """Handle a validation error.
        
        Args:
            error: Error that occurred
            data: Data that caused error
        """
        pass
        
    @abstractmethod
    async def get_validation_rules(self) -> Dict[str, Any]:
        """Get validation rules.
        
        Returns:
            Validation rules dictionary
        """
        pass

class BridgeValidator(BaseValidator):
    """Bridge-specific validator implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge validator.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(config)
        self.rules = self.config.get('validation_rules', {})
        
    async def validate(self, data: Dict[str, Any]) -> bool:
        """Validate bridge data.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check required fields
            if not self._validate_required_fields(data):
                return False
                
            # Check field types
            if not self._validate_field_types(data):
                return False
                
            # Check field values
            if not self._validate_field_values(data):
                return False
                
            return True
            
        except Exception as e:
            await self.handle_error(e, data)
            return False
            
    async def handle_error(self, error: Exception, data: Dict[str, Any]) -> None:
        """Handle a bridge validation error.
        
        Args:
            error: Error that occurred
            data: Data that caused error
        """
        self.logger.error(
            f"Validation error: {str(error)}",
            exc_info=True,
            extra={'data': data}
        )
        
    async def get_validation_rules(self) -> Dict[str, Any]:
        """Get bridge validation rules.
        
        Returns:
            Validation rules dictionary
        """
        return self.rules
        
    def _validate_required_fields(self, data: Dict[str, Any]) -> bool:
        """Validate required fields.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = self.rules.get('required_fields', [])
        return all(field in data for field in required_fields)
        
    def _validate_field_types(self, data: Dict[str, Any]) -> bool:
        """Validate field types.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        field_types = self.rules.get('field_types', {})
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False
        return True
        
    def _validate_field_values(self, data: Dict[str, Any]) -> bool:
        """Validate field values.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, False otherwise
        """
        field_values = self.rules.get('field_values', {})
        for field, value_rules in field_values.items():
            if field not in data:
                continue
                
            value = data[field]
            
            # Check min/max
            if 'min' in value_rules and value < value_rules['min']:
                return False
            if 'max' in value_rules and value > value_rules['max']:
                return False
                
            # Check pattern
            if 'pattern' in value_rules:
                import re
                if not re.match(value_rules['pattern'], str(value)):
                    return False
                    
            # Check enum
            if 'enum' in value_rules and value not in value_rules['enum']:
                return False
                
        return True 