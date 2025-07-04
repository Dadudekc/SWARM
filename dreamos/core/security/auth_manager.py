"""
Authentication Manager Module

Handles user and agent authentication, including token management,
login workflows, and permission checks.
"""

import time
import json
import threading
from typing import Dict, Optional, Any, Tuple, List
from datetime import datetime, timedelta
from pathlib import Path

from .security_config import SecurityConfig
from .identity_utils import IdentityUtils
from .session_manager import SessionManager

__all__ = [
    'AuthError',
    'AuthManager',
    'register_user',
    'authenticate',
    'validate_token',
    'get_user_info',
    'update_user_metadata',
    'assign_role',
    'remove_role',
    'save_users',
    'load_users',
    'is_locked_out',
    'record_failed_attempt'
]

class AuthError(Exception):
    """Base class for authentication errors."""
    pass

class AuthManager:
    """Manages authentication and authorization."""
    
    def __init__(self, config: Optional[SecurityConfig] = None):
        """Initialize authentication manager.
        
        Args:
            config: Optional security configuration. If not provided,
                   creates a new instance with default settings.
        """
        self.config = config or SecurityConfig()
        self.session_manager = SessionManager(config)
        self.users: Dict[str, Dict[str, Any]] = {}
        self.login_attempts: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        
    def register_user(self, username: str, password: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """Register a new user.
        
        Args:
            username: Username
            password: Password
            metadata: Optional user metadata
            
        Returns:
            Tuple of (success, error_message)
        """
        with self.lock:
            if username in self.users:
                return False, "Username already exists"
                
            # Validate password
            is_valid, error = IdentityUtils.validate_password(
                password,
                self.config.get_identity_config()
            )
            if not is_valid:
                return False, error
                
            # Hash password
            hashed_password, salt = IdentityUtils.hash_password(password)
            
            # Create user record
            self.users[username] = {
                'username': username,
                'password_hash': hashed_password,
                'salt': salt,
                'created_at': time.time(),
                'metadata': metadata or {},
                'roles': ['user']  # Default role
            }
            
            return True, None
            
    def authenticate(self, username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Authenticate a user.
        
        Args:
            username: Username
            password: Password
            
        Returns:
            Tuple of (success, error_message, session_token)
        """
        with self.lock:
            # Check if user exists
            if username not in self.users:
                return False, "Invalid username or password", None
                
            # Check login attempts
            if self.is_locked_out(username):
                return False, "Account temporarily locked", None
                
            # Verify password
            user = self.users[username]
            if not IdentityUtils.verify_password(password, user['password_hash'], user['salt']):
                self.record_failed_attempt(username)
                return False, "Invalid username or password", None
                
            # Create session
            token = self.session_manager.create_session(username, {
                'roles': user['roles'],
                'metadata': user['metadata']
            })
            
            return True, None, token
            
    def validate_token(self, token: str) -> bool:
        """Validate an authentication token.
        
        Args:
            token: Token to validate
            
        Returns:
            True if token is valid, False otherwise
        """
        return self.session_manager.validate_session(token)
        
    def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from token.
        
        Args:
            token: Authentication token
            
        Returns:
            User information dictionary if token valid, None otherwise
        """
        session = self.session_manager.get_session(token)
        if not session:
            return None
            
        username = session['user_id']
        if username not in self.users:
            return None
            
        user = self.users[username].copy()
        user.pop('password_hash', None)
        user.pop('salt', None)
        return user
        
    def update_user_metadata(self, token: str, metadata: Dict[str, Any]) -> bool:
        """Update user metadata.
        
        Args:
            token: Authentication token
            metadata: New metadata to merge with existing
            
        Returns:
            True if successful, False if token invalid
        """
        session = self.session_manager.get_session(token)
        if not session:
            return False
            
        username = session['user_id']
        if username not in self.users:
            return False
            
        with self.lock:
            self.users[username]['metadata'].update(metadata)
            return True
            
    def assign_role(self, token: str, username: str, role: str) -> Tuple[bool, Optional[str]]:
        """Assign a role to a user.
        
        Args:
            token: Authentication token of admin
            username: Username to assign role to
            role: Role to assign
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check if requester has admin role
        session = self.session_manager.get_session(token)
        if not session or 'admin' not in session['metadata'].get('roles', []):
            return False, "Permission denied"
            
        if username not in self.users:
            return False, "User not found"
            
        with self.lock:
            if role not in self.users[username]['roles']:
                self.users[username]['roles'].append(role)
            return True, None
            
    def remove_role(self, token: str, username: str, role: str) -> Tuple[bool, Optional[str]]:
        """Remove a role from a user.
        
        Args:
            token: Authentication token of admin
            username: Username to remove role from
            role: Role to remove
            
        Returns:
            Tuple of (success, error_message)
        """
        # Check if requester has admin role
        session = self.session_manager.get_session(token)
        if not session or 'admin' not in session['metadata'].get('roles', []):
            return False, "Permission denied"
            
        if username not in self.users:
            return False, "User not found"
            
        with self.lock:
            if role in self.users[username]['roles']:
                self.users[username]['roles'].remove(role)
            return True, None
            
    def is_locked_out(self, username: str) -> bool:
        """Check if a user is locked out due to too many failed attempts.
        
        Args:
            username: Username to check
            
        Returns:
            True if user is locked out, False otherwise
        """
        if username not in self.login_attempts:
            return False
            
        # Get recent attempts within lockout window
        now = time.time()
        window_start = now - self.config.get_identity_config()['lockout_window']
        recent_attempts = [t for t in self.login_attempts[username] if t > window_start]
        
        # Update attempts list
        self.login_attempts[username] = recent_attempts
        
        # Check if too many attempts
        max_attempts = self.config.get_identity_config()['max_login_attempts']
        return len(recent_attempts) >= max_attempts
        
    def record_failed_attempt(self, username: str) -> None:
        """Record a failed login attempt.
        
        Args:
            username: Username that failed to login
        """
        if username not in self.login_attempts:
            self.login_attempts[username] = []
        self.login_attempts[username].append(time.time())
        
    def save_users(self, path: str) -> None:
        """Save users to disk.
        
        Args:
            path: Path to save users
        """
        with self.lock:
            data = {
                'users': self.users,
                'timestamp': time.time()
            }
            
            with open(path, 'w') as f:
                json.dump(data, f)
                
    def load_users(self, path: str) -> None:
        """Load users from disk.
        
        Args:
            path: Path to load users from
        """
        if not Path(path).exists():
            return
            
        with self.lock:
            with open(path, 'r') as f:
                data = json.load(f)
                
            self.users = data['users'] 

# Create singleton instance
_auth_manager = AuthManager()

def register_user(username: str, password: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
    """Register a new user.
    
    Args:
        username: Username
        password: Password
        metadata: Optional user metadata
        
    Returns:
        Tuple of (success, error_message)
    """
    return _auth_manager.register_user(username, password, metadata)

def authenticate(username: str, password: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Authenticate a user.
    
    Args:
        username: Username
        password: Password
        
    Returns:
        Tuple of (success, error_message, session_token)
    """
    return _auth_manager.authenticate(username, password)

def validate_token(token: str) -> bool:
    """Validate an authentication token.
    
    Args:
        token: Token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    return _auth_manager.validate_token(token)

def get_user_info(token: str) -> Optional[Dict[str, Any]]:
    """Get user information from token.
    
    Args:
        token: Authentication token
        
    Returns:
        User information dictionary if token valid, None otherwise
    """
    return _auth_manager.get_user_info(token)

def update_user_metadata(token: str, metadata: Dict[str, Any]) -> bool:
    """Update user metadata.
    
    Args:
        token: Authentication token
        metadata: New metadata to merge with existing
        
    Returns:
        True if successful, False if token invalid
    """
    return _auth_manager.update_user_metadata(token, metadata)

def assign_role(token: str, username: str, role: str) -> Tuple[bool, Optional[str]]:
    """Assign a role to a user.
    
    Args:
        token: Authentication token of admin
        username: Username to assign role to
        role: Role to assign
        
    Returns:
        Tuple of (success, error_message)
    """
    return _auth_manager.assign_role(token, username, role)

def remove_role(token: str, username: str, role: str) -> Tuple[bool, Optional[str]]:
    """Remove a role from a user.
    
    Args:
        token: Authentication token of admin
        username: Username to remove role from
        role: Role to remove
        
    Returns:
        Tuple of (success, error_message)
    """
    return _auth_manager.remove_role(token, username, role)

def save_users(path: str) -> None:
    """Save users to a file.
    
    Args:
        path: Path to save users to
    """
    _auth_manager.save_users(path)

def load_users(path: str) -> None:
    """Load users from a file.
    
    Args:
        path: Path to load users from
    """
    _auth_manager.load_users(path)

def is_locked_out(username: str) -> bool:
    """Check if a user is locked out due to too many failed attempts.
    
    Args:
        username: Username to check
        
    Returns:
        True if user is locked out, False otherwise
    """
    with _auth_manager.lock:
        if username not in _auth_manager.login_attempts:
            return False
            
        # Get recent attempts within lockout window
        now = time.time()
        window = _auth_manager.config.get_identity_config().get('lockout_window', 300)  # 5 minutes default
        recent_attempts = [
            t for t in _auth_manager.login_attempts[username]
            if now - t < window
        ]
        
        # Update attempts list
        _auth_manager.login_attempts[username] = recent_attempts
        
        # Check if too many attempts
        max_attempts = _auth_manager.config.get_identity_config().get('max_login_attempts', 5)
        return len(recent_attempts) >= max_attempts

def record_failed_attempt(username: str) -> None:
    """Record a failed login attempt for a user.
    
    Args:
        username: Username to record attempt for
    """
    with _auth_manager.lock:
        if username not in _auth_manager.login_attempts:
            _auth_manager.login_attempts[username] = []
        _auth_manager.login_attempts[username].append(time.time()) 
