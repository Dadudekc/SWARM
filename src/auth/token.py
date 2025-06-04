"""
Token handling implementation.
"""

import time
import logging
import secrets
import hashlib
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from .base import ExpirableMixin

logger = logging.getLogger(__name__)

@dataclass
class TokenInfo(ExpirableMixin):
    """Represents token metadata."""
    user_id: str
    scope: str = "default"
    
    def __post_init__(self):
        """Initialize default values."""
        if self.data is None:
            self.data = {}
    
    @property
    def is_valid(self) -> bool:
        """Check if the token is still valid."""
        return datetime.now() < self.expires_at
    
    @property
    def time_remaining(self) -> float:
        """Get remaining time in seconds."""
        return max(0, (self.expires_at - datetime.now()).total_seconds())

class TokenHandler:
    """Handles token generation, validation, and refresh."""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        default_ttl: int = 3600,  # 1 hour
        min_token_length: int = 32
    ):
        """Initialize the token handler.
        
        Args:
            secret_key: Secret key for token signing (default: random)
            default_ttl: Default token lifetime in seconds
            min_token_length: Minimum token length in bytes
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.default_ttl = default_ttl
        self.min_token_length = min_token_length
        self._tokens: Dict[str, TokenInfo] = {}
    
    def generate_token(
        self,
        user_id: str,
        ttl: Optional[int] = None,
        scope: str = "default",
        data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a new token.
        
        Args:
            user_id: User identifier
            ttl: Token lifetime in seconds (default: default_ttl)
            scope: Token scope
            data: Optional token data
            
        Returns:
            Generated token
        """
        # Generate random token
        token = secrets.token_hex(max(self.min_token_length, 16))
        
        # Create token info
        now = datetime.now()
        token_info = TokenInfo(
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl or self.default_ttl),
            scope=scope,
            data=data or {}
        )
        
        # Store token
        self._tokens[token] = token_info
        logger.info(f"Generated token for user {user_id} with scope {scope}")
        
        return token
    
    def validate_token(self, token: str) -> bool:
        """Validate a token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        token_info = self._tokens.get(token)
        if token_info is None or not token_info.is_valid:
            return False
        return True
    
    def get_token_info(self, token: str) -> Optional[TokenInfo]:
        """Get token information.
        
        Args:
            token: Token to get info for
            
        Returns:
            TokenInfo if token is valid, None otherwise
        """
        token_info = self._tokens.get(token)
        if token_info is None or not token_info.is_valid:
            return None
        return token_info
    
    def refresh_token(self, token: str, ttl: Optional[int] = None) -> Optional[str]:
        """Refresh a token.
        
        Args:
            token: Token to refresh
            ttl: New token lifetime in seconds (default: default_ttl)
            
        Returns:
            New token if refresh successful, None otherwise
        """
        token_info = self._tokens.get(token)
        if token_info is None or not token_info.is_valid:
            return None
        
        # Generate new token
        new_token = self.generate_token(
            user_id=token_info.user_id,
            ttl=ttl,
            scope=token_info.scope,
            data=token_info.data
        )
        
        # Invalidate old token
        del self._tokens[token]
        logger.info(f"Refreshed token for user {token_info.user_id}")
        
        return new_token
    
    def invalidate_token(self, token: str) -> bool:
        """Invalidate a token.
        
        Args:
            token: Token to invalidate
            
        Returns:
            True if token was found and invalidated, False otherwise
        """
        if token in self._tokens:
            del self._tokens[token]
            logger.info("Token invalidated")
            return True
        return False
    
    def cleanup_expired(self) -> int:
        """Remove expired tokens.
        
        Returns:
            Number of tokens removed
        """
        expired = [
            token for token, info in self._tokens.items()
            if not info.is_valid
        ]
        for token in expired:
            del self._tokens[token]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired tokens")
        return len(expired)
    
    def _sign_token(self, token: str) -> str:
        """Sign a token with the secret key.
        
        Args:
            token: Token to sign
            
        Returns:
            Signed token
        """
        # In a real implementation, this would use a proper signing algorithm
        return hashlib.sha256(
            f"{token}:{self.secret_key}".encode()
        ).hexdigest() 