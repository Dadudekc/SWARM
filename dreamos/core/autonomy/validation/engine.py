"""Validation Engine
----------------
Validates responses and ensures they meet required criteria.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class ValidationEngine:
    """Engine for validating responses."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the validation engine.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.validators: List[callable] = []
        
    def add_validator(self, validator: callable):
        """Add a validator function.
        
        Args:
            validator: Function that takes a response and returns a ValidationResult
        """
        self.validators.append(validator)
        
    def validate(self, response: Dict[str, Any]) -> ValidationResult:
        """Validate a response.
        
        Args:
            response: The response to validate
            
        Returns:
            ValidationResult containing validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        for validator in self.validators:
            try:
                result = validator(response)
                if not result.is_valid:
                    errors.extend(result.errors)
                warnings.extend(result.warnings)
            except Exception as e:
                logger.error(f"Validator error: {e}")
                errors.append(f"Validator failed: {str(e)}")
                
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
        
    def validate_required_fields(self, response: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
        """Validate that required fields are present.
        
        Args:
            response: The response to validate
            required_fields: List of required field names
            
        Returns:
            ValidationResult
        """
        errors = []
        for field in required_fields:
            if field not in response:
                errors.append(f"Missing required field: {field}")
                
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
        
    def validate_field_type(self, response: Dict[str, Any], field: str, expected_type: type) -> ValidationResult:
        """Validate that a field has the expected type.
        
        Args:
            response: The response to validate
            field: Name of the field to check
            expected_type: Expected type of the field
            
        Returns:
            ValidationResult
        """
        if field not in response:
            return ValidationResult(
                is_valid=False,
                errors=[f"Missing field: {field}"],
                warnings=[]
            )
            
        if not isinstance(response[field], expected_type):
            return ValidationResult(
                is_valid=False,
                errors=[f"Field {field} has type {type(response[field])}, expected {expected_type}"],
                warnings=[]
            )
            
        return ValidationResult(
            is_valid=True,
            errors=[],
            warnings=[]
        )

    async def validate_agent_state(self, agent_id: str) -> bool:
        """Validate an agent's state for resumption.
        
        Args:
            agent_id: Agent ID to validate
            
        Returns:
            True if agent state is valid for resumption
        """
        try:
            # Load agent state
            state_path = Path(self.config.get("paths", {}).get("runtime", "data/runtime")) / "agents" / f"{agent_id}.json"
            if not state_path.exists():
                logger.error(f"Agent state file not found: {state_path}")
                return False
                
            with open(state_path) as f:
                state = json.load(f)
                
            # Validate required fields
            result = self.validate_required_fields(state, ["status", "last_update", "context"])
            if not result.is_valid:
                logger.error(f"Invalid agent state: {result.errors}")
                return False
                
            # Validate field types
            type_validations = [
                self.validate_field_type(state, "status", str),
                self.validate_field_type(state, "last_update", str),
                self.validate_field_type(state, "context", dict)
            ]
            
            for validation in type_validations:
                if not validation.is_valid:
                    logger.error(f"Invalid agent state types: {validation.errors}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating agent state: {e}")
            return False
            
    async def resume_agent(self, agent_id: str) -> bool:
        """Resume an agent from its saved state.
        
        Args:
            agent_id: Agent ID to resume
            
        Returns:
            True if agent was successfully resumed
        """
        try:
            # Load agent state
            state_path = Path(self.config.get("paths", {}).get("runtime", "data/runtime")) / "agents" / f"{agent_id}.json"
            if not state_path.exists():
                logger.error(f"Agent state file not found: {state_path}")
                return False
                
            with open(state_path) as f:
                state = json.load(f)
                
            # Update state to resuming
            state["status"] = "resuming"
            state["last_update"] = datetime.utcnow().isoformat()
            
            # Save updated state
            with open(state_path, "w") as f:
                json.dump(state, f, indent=2)
                
            # Trigger agent resume
            resume_path = Path(self.config.get("paths", {}).get("runtime", "data/runtime")) / "resume" / f"{agent_id}.json"
            resume_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(resume_path, "w") as f:
                json.dump({
                    "agent_id": agent_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": state["context"]
                }, f, indent=2)
                
            return True
            
        except Exception as e:
            logger.error(f"Error resuming agent: {e}")
            return False 
