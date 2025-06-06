"""
Session management implementation.
"""

import time
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from .base import ExpirableMixin

logger = logging.getLogger(__name__)

@dataclass
class Session:
    """Represents an active user session."""
    user_id: str
    created_at: datetime
    expires_at: datetime
    data: Optional[Dict[str, Any]] = None
    
    def extend(self, seconds: int) -> None:
        """Extend session lifetime.
        
        Args:
            seconds: Number of seconds to extend by
        """
        self.expires_at += timedelta(seconds=seconds)
        logger.debug(f"Extended session for user {self.user_id} by {seconds}s")
        
    @property
    def is_valid(self) -> bool:
        """Check if the session is still valid."""
        return datetime.now() < self.expires_at
    
    @property
    def time_remaining(self) -> float:
        """Get remaining time in seconds."""
        return max(0, (self.expires_at - datetime.now()).total_seconds())

class SessionManager:
    """Manages user sessions with automatic cleanup."""
    
    def __init__(
        self,
        cleanup_interval: int = 300,  # 5 minutes
        default_ttl: int = 3600,      # 1 hour
        max_sessions: int = 10000
    ):
        """Initialize the session manager.
        
        Args:
            cleanup_interval: Seconds between cleanup runs
            default_ttl: Default session lifetime in seconds
            max_sessions: Maximum number of active sessions
        """
        self.cleanup_interval = cleanup_interval
        self.default_ttl = default_ttl
        self.max_sessions = max_sessions
        self._sessions: Dict[str, Session] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._stop_cleanup = threading.Event()
    
    def start_cleanup(self) -> None:
        """Start the cleanup thread."""
        if self._cleanup_thread is not None:
            return
        
        def cleanup_loop():
            while not self._stop_cleanup.is_set():
                self.cleanup_expired()
                time.sleep(self.cleanup_interval)
        
        self._cleanup_thread = threading.Thread(
            target=cleanup_loop,
            daemon=True,
            name="SessionCleanup"
        )
        self._cleanup_thread.start()
        logger.info("Session cleanup thread started")
    
    def stop_cleanup(self) -> None:
        """Stop the cleanup thread."""
        if self._cleanup_thread is None:
            return
        
        self._stop_cleanup.set()
        self._cleanup_thread.join()
        self._cleanup_thread = None
        logger.info("Session cleanup thread stopped")
    
    def create_session(
        self,
        user_id: str,
        ttl: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Session:
        """Create a new session.
        
        Args:
            user_id: User identifier
            ttl: Session lifetime in seconds (default: default_ttl)
            data: Optional session data
            
        Returns:
            Created session object
            
        Raises:
            ValueError: If max_sessions limit is reached
        """
        with self._lock:
            if len(self._sessions) >= self.max_sessions:
                raise ValueError("Maximum number of sessions reached")
            
            session_id = self._generate_session_id()
            now = datetime.now()
            session = Session(
                user_id=user_id,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl or self.default_ttl),
                data=data or {}
            )
            self._sessions[session_id] = session
            logger.info(f"Created session {session_id} for user {user_id}")
            return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session object if found and valid, None otherwise
        """
        session = self._sessions.get(session_id)
        if session is None or not session.is_valid:
            return None
        return session
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was found and invalidated, False otherwise
        """
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.info(f"Invalidated session {session_id}")
                return True
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired sessions.
        
        Returns:
            Number of sessions removed
        """
        with self._lock:
            expired = [
                session_id for session_id, session in self._sessions.items()
                if not session.is_valid
            ]
            for session_id in expired:
                del self._sessions[session_id]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
            return len(expired)
    
    def _generate_session_id(self) -> str:
        """Generate a unique session identifier.
        
        Returns:
            Unique session ID
        """
        # In a real implementation, this would use a more robust method
        return f"sess_{int(time.time() * 1000)}_{len(self._sessions)}" 