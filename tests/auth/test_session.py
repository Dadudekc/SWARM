"""
Tests for the session manager implementation.
"""

import pytest
import time
from datetime import datetime, timedelta
from typing import Dict, Any
from dreamos.core.security.session_manager import SessionManager, SessionError

def test_session_manager_initialization():
    """Test SessionManager initialization with config."""
    config = {
        'max_sessions': 1000,
        'session_timeout': 3600,
        'cleanup_interval': 300
    }
    manager = SessionManager(config)
    assert manager.max_sessions == 1000
    assert manager.session_timeout == 3600
    assert manager.cleanup_interval == 300

def test_session_manager_default_config():
    """Test SessionManager initialization with default config."""
    manager = SessionManager()
    assert manager.max_sessions == 1000
    assert manager.session_timeout == 3600
    assert manager.cleanup_interval == 300

def test_session_creation():
    """Test session creation and retrieval."""
    manager = SessionManager()
    session_data = {
        'user_id': 'test_user',
        'platform': 'test_platform',
        'metadata': {'ip': '127.0.0.1'}
    }
    session_id = manager.create_session(session_data)
    assert session_id is not None
    retrieved = manager.get_session(session_id)
    assert retrieved['user_id'] == 'test_user'
    assert retrieved['platform'] == 'test_platform'
    assert retrieved['metadata']['ip'] == '127.0.0.1'

def test_session_expiration():
    """Test session expiration handling."""
    manager = SessionManager({'session_timeout': 1})
    session_data = {'user_id': 'test_user'}
    session_id = manager.create_session(session_data)
    time.sleep(2)
    with pytest.raises(SessionError):
        manager.get_session(session_id)

def test_session_cleanup():
    """Test automatic session cleanup."""
    manager = SessionManager({
        'session_timeout': 1,
        'cleanup_interval': 1
    })
    session_data = {'user_id': 'test_user'}
    session_id = manager.create_session(session_data)
    time.sleep(2)
    manager.cleanup_expired_sessions()
    with pytest.raises(SessionError):
        manager.get_session(session_id)

def test_session_update():
    """Test session data update."""
    manager = SessionManager()
    session_data = {'user_id': 'test_user'}
    session_id = manager.create_session(session_data)
    updated_data = {'user_id': 'test_user', 'last_activity': datetime.now()}
    manager.update_session(session_id, updated_data)
    retrieved = manager.get_session(session_id)
    assert 'last_activity' in retrieved

def test_session_deletion():
    """Test session deletion."""
    manager = SessionManager()
    session_data = {'user_id': 'test_user'}
    session_id = manager.create_session(session_data)
    assert manager.delete_session(session_id) is True
    with pytest.raises(SessionError):
        manager.get_session(session_id) 
