"""
Authentication manager implementation.
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from .interface import AbstractAuthInterface, AuthError
from .retry import RetryMechanism

logger = logging.getLogger(__name__)

class AuthManager(AbstractAuthInterface):
    """Authentication manager implementing the platform-agnostic interface."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the auth manager with configuration.
        
        Args:
            config: Optional configuration dictionary containing:
                - max_retries: Maximum number of retry attempts (default: 3)
                - retry_delay: Base delay in seconds for retries (default: 1.0)
                - session_timeout: Session timeout in seconds (default: 3600)
        """
        self.config = config or {}
        self.max_retries = self.config.get('max_retries', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        self.session_timeout = self.config.get('session_timeout', 3600)
        self._sessions = {}
        self._retry = RetryMechanism(
            max_retries=self.max_retries,
            base_delay=self.retry_delay
        )
    
    def _attempt_login(self, username: str, password: str) -> Dict[str, Any]:
        """Attempt a single login operation.
        
        This method should be implemented by platform-specific auth providers.
        
        Args:
            username: The username to authenticate
            password: The password to authenticate with
            
        Returns:
            Dict containing session information
            
        Raises:
            AuthError: If authentication fails
        """
        raise NotImplementedError("Platform-specific login not implemented")
    
    def login(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate a user with retry logic.
        
        Args:
            username: The username to authenticate
            password: The password to authenticate with
            
        Returns:
            Dict containing session information
            
        Raises:
            AuthError: If authentication fails after all retries
        """
        def login_operation():
            try:
                result = self._attempt_login(username, password)
                session_id = result.get('session_id')
                if session_id:
                    self._sessions[session_id] = {
                        'user_id': username,
                        'created_at': datetime.now(),
                        'expires_at': datetime.now() + timedelta(seconds=self.session_timeout)
                    }
                return result
            except Exception as e:
                logger.warning(f"Login attempt failed: {str(e)}")
                raise AuthError(f"Authentication failed: {str(e)}")
        
        try:
            return self._retry.execute(login_operation)
        except Exception as e:
            logger.error(f"Login failed after {self.max_retries} attempts: {str(e)}")
            raise AuthError(f"Authentication failed after {self.max_retries} attempts")
    
    def logout(self, session_id: str) -> bool:
        """Invalidate a user session.
        
        Args:
            session_id: The session identifier to invalidate
            
        Returns:
            True if session was successfully invalidated, False otherwise
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Session {session_id} invalidated")
            return True
        logger.warning(f"Attempted to invalidate non-existent session {session_id}")
        return False
    
    def verify_session(self, session_id: str) -> bool:
        """Verify if a session is valid.
        
        Args:
            session_id: The session identifier to verify
            
        Returns:
            True if session is valid, False otherwise
        """
        if session_id not in self._sessions:
            return False
        session = self._sessions[session_id]
        is_valid = datetime.now() < session['expires_at']
        if not is_valid:
            logger.info(f"Session {session_id} expired")
            del self._sessions[session_id]
        return is_valid
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an authentication token.
        
        This method should be implemented by platform-specific auth providers.
        
        Args:
            token: The token to refresh
            
        Returns:
            New token if refresh successful, None otherwise
            
        Raises:
            AuthError: If token refresh fails
        """
        raise NotImplementedError("Platform-specific token refresh not implemented")
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired = [
            session_id for session_id, session in self._sessions.items()
            if now >= session['expires_at']
        ]
        for session_id in expired:
            del self._sessions[session_id]
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")
        return len(expired) 