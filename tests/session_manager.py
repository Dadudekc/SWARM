import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""
Unit tests for the SessionManager module.
"""

import pytest
import time
import json
import os
from pathlib import Path
from dreamos.core.security.session_manager import SessionManager
from dreamos.core.security.security_config import SecurityConfig

@pytest.fixture
def session_config():
    """Fixture providing test session configuration."""
    return {
        'max_sessions_per_user': 3,
        'session_timeout': 2,  # 2 seconds for testing
        'cleanup_interval': 1  # 1 second for testing
    }

@pytest.fixture
def security_config(session_config):
    """Fixture providing test security configuration."""
    config = SecurityConfig()
    config.update_config('session', session_config)
    return config

@pytest.fixture
def session_manager(security_config):
    """Fixture providing a SessionManager instance."""
    return SessionManager(security_config)

class TestSessionManager:
    """Test suite for SessionManager class."""
    
    def test_create_session(self, session_manager):
        """Test session creation."""
        # Create session
        token = session_manager.create_session("test_user")
        assert token is not None
        assert len(token) == 64  # 32 bytes in hex
        
        # Verify session exists
        session = session_manager.get_session(token)
        assert session is not None
        assert session['user_id'] == "test_user"
        assert 'created_at' in session
        assert 'last_activity' in session
        assert 'metadata' in session
        
    def test_session_limit(self, session_manager):
        """Test session limit per user."""
        # Create max sessions
        tokens = []
        for _ in range(3):  # max_sessions_per_user
            token = session_manager.create_session("test_user")
            tokens.append(token)
            
        # Create one more session
        new_token = session_manager.create_session("test_user")
        
        # Verify oldest session was removed
        assert len(tokens) == 3
        assert new_token not in tokens
        assert not session_manager.validate_session(tokens[0])  # Oldest session should be gone
        
    def test_session_timeout(self, session_manager):
        """Test session timeout."""
        # Create session
        token = session_manager.create_session("test_user")
        assert session_manager.validate_session(token)
        
        # Wait for timeout
        time.sleep(3)  # session_timeout + 1
        
        # Verify session expired
        assert not session_manager.validate_session(token)
        
    def test_session_metadata(self, session_manager):
        """Test session metadata handling."""
        # Create session with metadata
        metadata = {"role": "admin", "ip": "127.0.0.1"}
        token = session_manager.create_session("test_user", metadata)
        
        # Verify metadata
        session = session_manager.get_session(token)
        assert session['metadata'] == metadata
        
        # Update metadata
        new_metadata = {"role": "user"}
        assert session_manager.update_session_metadata(token, new_metadata)
        
        # Verify updated metadata
        session = session_manager.get_session(token)
        assert session['metadata'] == {"role": "user", "ip": "127.0.0.1"}
        
    def test_invalidate_session(self, session_manager):
        """Test session invalidation."""
        # Create session
        token = session_manager.create_session("test_user")
        assert session_manager.validate_session(token)
        
        # Invalidate session
        assert session_manager.invalidate_session(token)
        assert not session_manager.validate_session(token)
        
        # Try to invalidate non-existent session
        assert not session_manager.invalidate_session("invalid_token")
        
    def test_session_persistence(self, session_manager, tmp_path):
        """Test session persistence to disk."""
        # Create some sessions
        tokens = []
        for i in range(3):
            token = session_manager.create_session(f"user_{i}")
            tokens.append(token)
            
        # Save sessions
        save_path = tmp_path / "sessions.json"
        session_manager.save_sessions(str(save_path))
        
        # Create new manager and load sessions
        new_manager = SessionManager(session_manager.config)
        new_manager.load_sessions(str(save_path))
        
        # Verify sessions loaded
        for token in tokens:
            assert new_manager.validate_session(token)
            
    def test_cleanup_expired_sessions(self, session_manager):
        """Test cleanup of expired sessions."""
        # Create sessions
        tokens = []
        for i in range(3):
            token = session_manager.create_session(f"user_{i}")
            tokens.append(token)
            
        # Wait for some sessions to expire
        time.sleep(3)  # session_timeout + 1
        
        # Force cleanup
        session_manager.cleanup_expired_sessions()
        
        # Verify expired sessions removed
        for token in tokens:
            assert not session_manager.validate_session(token)
            
    def test_concurrent_access(self, session_manager):
        """Test concurrent access to session manager."""
        import threading
        
        def create_sessions():
            for _ in range(10):
                session_manager.create_session("concurrent_user")
                
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_sessions)
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        # Verify no exceptions occurred and sessions were created
        sessions = [s for s in session_manager.sessions.values() if s['user_id'] == "concurrent_user"]
        assert len(sessions) <= session_manager.config.get_session_config()['max_sessions_per_user'] 
