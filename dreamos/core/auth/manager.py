"""Authentication manager for handling user authentication and authorization."""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import jwt
import time
from pathlib import Path
import json

from .interface import AbstractAuthInterface, AuthError
from .session import Session, SessionManager
from .token import TokenInfo, TokenHandler

@dataclass
class AuthConfig:
    """Configuration for authentication."""
    secret_key: str
    token_expiry: int = 3600  # 1 hour
    refresh_token_expiry: int = 604800  # 1 week
    session_expiry: int = 86400  # 24 hours
    config_path: Path = Path("config/auth.json")

class AuthManager(AbstractAuthInterface):
    """Manages authentication and authorization."""
    
    def __init__(self, config: Optional[AuthConfig] = None):
        """Initialize the auth manager."""
        self.config = config or self._load_config()
        self.token_handler = TokenHandler(self.config)
        self.session_manager = SessionManager(self.config)
    
    def _load_config(self) -> AuthConfig:
        """Load auth configuration from file."""
        if not self.config_path.exists():
            raise AuthError("Auth config file not found")
        
        with open(self.config_path) as f:
            data = json.load(f)
        
        return AuthConfig(
            secret_key=data["secret_key"],
            token_expiry=data.get("token_expiry", 3600),
            refresh_token_expiry=data.get("refresh_token_expiry", 604800),
            session_expiry=data.get("session_expiry", 86400),
            config_path=self.config_path
        )
    
    def authenticate(self, credentials: Dict[str, Any]) -> TokenInfo:
        """Authenticate a user and return token info."""
        # TODO: Implement actual authentication logic
        return self.token_handler.create_tokens(credentials)
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate a JWT token."""
        try:
            return jwt.decode(
                token,
                self.config.secret_key,
                algorithms=["HS256"]
            )
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {e}")
    
    def refresh_token(self, refresh_token: str) -> TokenInfo:
        """Refresh an access token using a refresh token."""
        try:
            payload = self.validate_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthError("Invalid refresh token")
            
            return self.token_handler.create_tokens({
                "user_id": payload["user_id"]
            })
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid refresh token: {e}")
    
    def create_session(self, user_id: str) -> Session:
        """Create a new session for a user."""
        return self.session_manager.create_session(user_id)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self.session_manager.get_session(session_id)
    
    def invalidate_session(self, session_id: str) -> None:
        """Invalidate a session."""
        self.session_manager.invalidate_session(session_id) 
