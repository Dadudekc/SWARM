"""
Token handling implementation.
"""

import time
import logging
import secrets
import hashlib
import hmac
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from .base import ExpirableMixin

logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    """Represents token metadata."""
    user_id: str
    created_at: datetime
    expires_at: datetime
    scope: str = "default"
    data: Dict[str, Any] = None

    @property
    def is_valid(self) -> bool:
        """Check if token is still valid."""
        return datetime.now() < self.expires_at

    @property
    def time_remaining(self) -> timedelta:
        """Get remaining time until expiration."""
        return self.expires_at - datetime.now()

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
            secret_key: Secret key for token signing (default: from env or random)
            default_ttl: Default token lifetime in seconds
            min_token_length: Minimum token length in bytes
        """
        self.secret_key = secret_key or self._load_secret_key()
        self.default_ttl = default_ttl
        self.min_token_length = min_token_length
        self._tokens: Dict[str, TokenInfo] = {}
    
    def _load_secret_key(self) -> str:
        """Load secret key from environment or generate new one."""
        secret = os.getenv("DREAMOS_SECRET")
        if not secret:
            logger.warning("DREAMOS_SECRET not found in environment, generating new key")
            secret = secrets.token_urlsafe(32)
        return secret
    
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
        # Generate random token using URL-safe base64
        raw_token = secrets.token_urlsafe(max(self.min_token_length, 32))
        
        # Create token info
        now = datetime.now()
        token_info = TokenInfo(
            user_id=user_id,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl or self.default_ttl),
            scope=scope,
            data=data or {}
        )
        
        # Sign token
        signed_token = self._sign_token(raw_token)
        
        # Store token
        self._tokens[signed_token] = token_info
        logger.info(f"Generated token for user {user_id} with scope {scope}")
        
        return signed_token
    
    def validate_token(self, token: str) -> bool:
        """Validate a token using constant-time comparison.
        
        Args:
            token: Token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        token_info = self._tokens.get(token)
        if token_info is None or not token_info.is_valid:
            return False
            
        # Verify token signature using constant-time comparison
        try:
            raw_token = token.split('.')[0]  # Extract raw token before signature
            expected_signature = self._sign_token(raw_token)
            return hmac.compare_digest(token, expected_signature)
        except Exception:
            return False
    
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
        """Sign a token with the secret key using HMAC-SHA256.
        
        Args:
            token: Token to sign
            
        Returns:
            Signed token
        """
        signer = hmac.new(
            self.secret_key.encode(),
            token.encode(),
            hashlib.sha256
        )
        return f"{token}.{signer.hexdigest()}" 