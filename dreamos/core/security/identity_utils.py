"""
Identity Utilities Module

Provides helper functions for user and agent identity management,
including validation, formatting, and security checks.
"""

import re
import hashlib
import secrets
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

class IdentityUtils:
    """Utility functions for identity management."""
    
    @staticmethod
    def generate_agent_id(prefix: str = "agent") -> str:
        """Generate a unique agent identifier.
        
        Args:
            prefix: Optional prefix for the agent ID
            
        Returns:
            A unique agent identifier string
        """
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_suffix = secrets.token_hex(4)
        return f"{prefix}-{timestamp}-{random_suffix}"
        
    @staticmethod
    def validate_password(password: str, config: dict) -> Tuple[bool, Optional[str]]:
        """Validate password against security requirements.
        
        Args:
            password: Password to validate
            config: Identity configuration dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < config['min_password_length']:
            return False, f"Password must be at least {config['min_password_length']} characters"
            
        if config['require_special_chars'] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
            
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
            
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
            
        if not re.search(r'[0-9]', password):
            return False, "Password must contain at least one number"
            
        return True, None
        
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash a password with a salt.
        
        Args:
            password: Password to hash
            salt: Optional salt. If not provided, generates a new one.
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
            
        # Use PBKDF2 with SHA-256
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        )
        
        return key.hex(), salt
        
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """Verify a password against its hash and salt.
        
        Args:
            password: Password to verify
            hashed_password: Stored hash to check against
            salt: Salt used in the hash
            
        Returns:
            True if password matches, False otherwise
        """
        new_hash, _ = IdentityUtils.hash_password(password, salt)
        return new_hash == hashed_password
        
    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a secure random token.
        
        Args:
            length: Length of token in bytes
            
        Returns:
            A secure random token string
        """
        return secrets.token_hex(length)
        
    @staticmethod
    def format_agent_name(name: str) -> str:
        """Format an agent name to be consistent.
        
        Args:
            name: Raw agent name
            
        Returns:
            Formatted agent name
        """
        # Remove special characters and extra spaces
        name = re.sub(r'[^a-zA-Z0-9\s-]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Convert to title case
        return name.title() 
