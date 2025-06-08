"""
Tests for the platform-agnostic authentication interface.
"""

import pytest
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
        """Authenticate a user and return session information."""
        pass
    
    @abstractmethod
    def logout(self, session_id: str) -> bool:
        """Invalidate a user session."""
        pass
    
    @abstractmethod
    def verify_session(self, session_id: str) -> bool:
        """Verify if a session is valid."""
        pass
    
    @abstractmethod
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh an authentication token."""
        pass

def test_auth_interface_contract():
    """Test that interface contract is enforced."""
    class IncompleteAuth(AbstractAuthInterface):
        pass  # Missing required methods
    
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteAuth()

def test_auth_interface_methods():
    """Test that AuthInterface methods are properly defined."""
    assert hasattr(AbstractAuthInterface, 'login')
    assert hasattr(AbstractAuthInterface, 'logout')
    assert hasattr(AbstractAuthInterface, 'verify_session')
    assert hasattr(AbstractAuthInterface, 'refresh_token')

def test_auth_interface_method_signatures():
    """Test that AuthInterface methods have correct signatures."""
    # Get method signatures
    login_sig = AbstractAuthInterface.login.__annotations__
    logout_sig = AbstractAuthInterface.logout.__annotations__
    verify_sig = AbstractAuthInterface.verify_session.__annotations__
    refresh_sig = AbstractAuthInterface.refresh_token.__annotations__
    
    # Verify login signature
    assert 'username' in login_sig
    assert 'password' in login_sig
    assert login_sig['return'] == Dict[str, Any]
    
    # Verify logout signature
    assert 'session_id' in logout_sig
    assert logout_sig['return'] == bool
    
    # Verify verify_session signature
    assert 'session_id' in verify_sig
    assert verify_sig['return'] == bool
    
    # Verify refresh_token signature
    assert 'token' in refresh_sig
    assert refresh_sig['return'] == Optional[str]

def test_auth_interface_implementation():
    """Test a valid implementation of the AuthInterface."""
    class TestAuth(AbstractAuthInterface):
        def login(self, username: str, password: str) -> Dict[str, Any]:
            return {"token": "test_token", "session_id": "test_session"}
        
        def logout(self, session_id: str) -> bool:
            return True
        
        def verify_session(self, session_id: str) -> bool:
            return True
        
        def refresh_token(self, token: str) -> Optional[str]:
            return "new_token"
    
    auth = TestAuth()
    assert auth.login("user", "pass")["token"] == "test_token"
    assert auth.logout("session") is True
    assert auth.verify_session("session") is True
    assert auth.refresh_token("token") == "new_token" 
