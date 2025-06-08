"""
Session Management Module

Exports session management functionality from the security module.
"""

from ..security.session_manager import SessionManager
from ..security.security_config import SecurityConfig
import time

class Session:
    """Session class for managing user sessions."""
    
    def __init__(self, token: str, user_id: str, metadata: dict = None):
        """Initialize a session.
        
        Args:
            token: Session token
            user_id: User identifier
            metadata: Optional session metadata
        """
        self.token = token
        self.user_id = user_id
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_activity = time.time()

# Export the SessionManager class
__all__ = ['Session', 'SessionManager', 'SecurityConfig'] 
