"""
Session Manager Module

Handles session creation, validation, and cleanup for both users and agents.
Provides session persistence and recovery capabilities.
"""

import time
import json
import threading
from typing import Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from .security_config import SecurityConfig
from .identity_utils import IdentityUtils

class SessionError(Exception):
    """Base class for session management errors."""
    pass

class SessionManager:
    """Manages user and agent sessions."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize session manager.
        
        Args:
            config: Optional security configuration. If not provided,
                   creates a new instance with default settings.
        """
        self.config = config or SecurityConfig()
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self) -> None:
        """Start background thread for session cleanup."""
        def cleanup_loop():
            while True:
                self.cleanup_expired_sessions()
                time.sleep(self.config.get_session_config()['cleanup_interval'])
                
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
        
    def create_session(self, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session for a user.
        
        Args:
            user_id: User identifier
            metadata: Optional session metadata
            
        Returns:
            Session token
        """
        with self.lock:
            # Check session limit
            user_sessions = [s for s in self.sessions.values() if s['user_id'] == user_id]
            if len(user_sessions) >= self.config.get_session_config()['max_sessions_per_user']:
                # Remove oldest session
                oldest = min(user_sessions, key=lambda s: s['created_at'])
                del self.sessions[oldest['token']]
                
            # Create new session
            token = IdentityUtils.generate_token()
            session = {
                'token': token,
                'user_id': user_id,
                'created_at': time.time(),
                'last_activity': time.time(),
                'metadata': metadata or {}
            }
            
            self.sessions[token] = session
            return token
            
    def validate_session(self, token: str) -> bool:
        """Validate a session token.
        
        Args:
            token: Session token to validate
            
        Returns:
            True if session is valid, False otherwise
        """
        with self.lock:
            if token not in self.sessions:
                return False
                
            session = self.sessions[token]
            timeout = self.config.get_session_config()['session_timeout']
            
            # Check if session has expired
            if time.time() - session['last_activity'] > timeout:
                del self.sessions[token]
                return False
                
            # Update last activity
            session['last_activity'] = time.time()
            return True
            
    def get_session(self, token: str) -> Optional[Dict[str, Any]]:
        """Get session data.
        
        Args:
            token: Session token
            
        Returns:
            Session data dictionary if valid, None otherwise
        """
        with self.lock:
            if not self.validate_session(token):
                return None
            return self.sessions[token].copy()
            
    def update_session_metadata(self, token: str, metadata: Dict[str, Any]) -> bool:
        """Update session metadata.
        
        Args:
            token: Session token
            metadata: New metadata to merge with existing
            
        Returns:
            True if successful, False if session invalid
        """
        with self.lock:
            if not self.validate_session(token):
                return False
                
            self.sessions[token]['metadata'].update(metadata)
            return True
            
    def invalidate_session(self, token: str) -> bool:
        """Invalidate a session.
        
        Args:
            token: Session token to invalidate
            
        Returns:
            True if session was found and invalidated, False otherwise
        """
        with self.lock:
            if token in self.sessions:
                del self.sessions[token]
                return True
            return False
            
    def cleanup_expired_sessions(self) -> None:
        """Remove expired sessions."""
        with self.lock:
            timeout = self.config.get_session_config()['session_timeout']
            current_time = time.time()
            
            expired = [
                token for token, session in self.sessions.items()
                if current_time - session['last_activity'] > timeout
            ]
            
            for token in expired:
                del self.sessions[token]
                
    def save_sessions(self, path: str) -> None:
        """Save sessions to disk.
        
        Args:
            path: Path to save sessions
        """
        with self.lock:
            data = {
                'sessions': self.sessions,
                'timestamp': time.time()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f)
                
    def load_sessions(self, path: str) -> None:
        """Load sessions from disk.
        
        Args:
            path: Path to load sessions from
        """
        if not Path(path).exists():
            return
            
        with self.lock:
            with open(path, 'r') as f:
                data = json.load(f)
                
            # Only load non-expired sessions
            timeout = self.config.get_session_config()['session_timeout']
            current_time = time.time()
            
            self.sessions = {
                token: session
                for token, session in data['sessions'].items()
                if current_time - session['last_activity'] <= timeout
            } 
