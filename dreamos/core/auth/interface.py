"""
Core authentication interface definitions.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

class AuthError(Exception):
    """Base class for authentication errors."""
    pass

class AbstractAuthInterface(ABC):
    """Abstract base class defining the authentication interface."""
    
    @abstractmethod
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user and return session information.
        
        Args:
            username: The username to authenticate
            password: The password to authenticate with
            
        Returns:
            Dict containing session information including:
            - token: Authentication token
            - session_id: Unique session identifier
            - expires_at: Session expiration timestamp
            
        Raises:
            AuthError: If authentication fails
        """
        pass
    
    @abstractmethod
    def logout(self, session_id: str) -> bool:
        """Invalidate a user session.
        
        Args:
            session_id: The session identifier to invalidate
            
        Returns:
            True if session was successfully invalidated, False otherwise
        """
        pass
    
    @abstractmethod
    def verify_session(self, session_id: str) -> bool:
        """Verify if a session is valid.
        
        Args:
            session_id: The session identifier to verify
            
        Returns:
            True if session is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an authentication token.
        
        Args:
            token: The token to refresh
            
        Returns:
            New token if refresh successful, None otherwise
        """
        pass 
