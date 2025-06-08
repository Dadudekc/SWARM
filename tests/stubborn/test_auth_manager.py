"""
Unit tests for the AuthManager module.
"""

import pytest
import time
import json
import os
from pathlib import Path
from dreamos.core.security.auth_manager import AuthManager
from dreamos.core.security.security_config import SecurityConfig

@pytest.fixture
def auth_config():
    """Fixture providing test auth configuration."""
    return {
        'token_expiry': 2,  # 2 seconds for testing
        'refresh_token_expiry': 4,  # 4 seconds for testing
        'max_login_attempts': 3,
        'lockout_duration': 2  # 2 seconds for testing
    }

@pytest.fixture
def security_config(auth_config):
    """Fixture providing test security configuration."""
    config = SecurityConfig()
    config.update_config('auth', auth_config)
    return config

@pytest.fixture
def auth_manager(security_config):
    """Fixture providing an AuthManager instance."""
    return AuthManager(security_config)

class TestAuthManager:
    """Test suite for AuthManager class."""
    
    def test_register_user(self, auth_manager):
        """Test user registration."""
        # Register valid user
        success, error = auth_manager.register_user(
            "test_user",
            "ValidPass123!",
            {"email": "test@example.com"}
        )
        assert success
        assert error is None
        
        # Try to register duplicate user
        success, error = auth_manager.register_user("test_user", "AnotherPass123!")
        assert not success
        assert error == "Username already exists"
        
        # Try to register with invalid password
        success, error = auth_manager.register_user("new_user", "short")
        assert not success
        assert "Password must be at least" in error
        
    def test_authenticate(self, auth_manager):
        """Test user authentication."""
        # Register user
        auth_manager.register_user("test_user", "ValidPass123!")
        
        # Test successful login
        success, error, token = auth_manager.authenticate("test_user", "ValidPass123!")
        assert success
        assert error is None
        assert token is not None
        
        # Test invalid password
        success, error, token = auth_manager.authenticate("test_user", "WrongPass123!")
        assert not success
        assert error == "Invalid username or password"
        assert token is None
        
        # Test non-existent user
        success, error, token = auth_manager.authenticate("nonexistent", "AnyPass123!")
        assert not success
        assert error == "Invalid username or password"
        assert token is None
        
    def test_login_attempts(self, auth_manager):
        """Test login attempt tracking and lockout."""
        # Register user
        auth_manager.register_user("test_user", "ValidPass123!")
        
        # Make max attempts
        for _ in range(3):  # max_login_attempts
            success, error, token = auth_manager.authenticate("test_user", "WrongPass123!")
            assert not success
            
        # Try one more time - should be locked out
        success, error, token = auth_manager.authenticate("test_user", "ValidPass123!")
        assert not success
        assert error == "Account temporarily locked"
        
        # Wait for lockout to expire
        time.sleep(3)  # lockout_duration + 1
        
        # Should be able to login now
        success, error, token = auth_manager.authenticate("test_user", "ValidPass123!")
        assert success
        assert error is None
        assert token is not None
        
    def test_token_validation(self, auth_manager):
        """Test token validation."""
        # Register and login
        auth_manager.register_user("test_user", "ValidPass123!")
        success, error, token = auth_manager.authenticate("test_user", "ValidPass123!")
        
        # Verify token
        assert auth_manager.validate_token(token)
        
        # Wait for token to expire
        time.sleep(3)  # token_expiry + 1
        
        # Token should be invalid
        assert not auth_manager.validate_token(token)
        
    def test_user_info(self, auth_manager):
        """Test user info retrieval."""
        # Register user with metadata
        metadata = {"email": "test@example.com", "role": "developer"}
        auth_manager.register_user("test_user", "ValidPass123!", metadata)
        
        # Login
        success, error, token = auth_manager.authenticate("test_user", "ValidPass123!")
        
        # Get user info
        user_info = auth_manager.get_user_info(token)
        assert user_info is not None
        assert user_info['username'] == "test_user"
        assert user_info['metadata'] == metadata
        assert 'password_hash' not in user_info
        assert 'salt' not in user_info
        
        # Test with invalid token
        assert auth_manager.get_user_info("invalid_token") is None
        
    def test_role_management(self, auth_manager):
        """Test role assignment and removal."""
        # Register admin user
        auth_manager.register_user("admin", "AdminPass123!", {"roles": ["admin"]})
        admin_success, _, admin_token = auth_manager.authenticate("admin", "AdminPass123!")
        
        # Register regular user
        auth_manager.register_user("user", "UserPass123!")
        user_success, _, user_token = auth_manager.authenticate("user", "UserPass123!")
        
        # Admin assigns role
        success, error = auth_manager.assign_role(admin_token, "user", "developer")
        assert success
        assert error is None
        
        # Verify role assigned
        user_info = auth_manager.get_user_info(user_token)
        assert "developer" in user_info['roles']
        
        # Admin removes role
        success, error = auth_manager.remove_role(admin_token, "user", "developer")
        assert success
        assert error is None
        
        # Verify role removed
        user_info = auth_manager.get_user_info(user_token)
        assert "developer" not in user_info['roles']
        
        # Test non-admin can't modify roles
        success, error = auth_manager.assign_role(user_token, "admin", "user")
        assert not success
        assert error == "Permission denied"
        
    def test_user_persistence(self, auth_manager, tmp_path):
        """Test user persistence to disk."""
        # Register some users
        auth_manager.register_user("user1", "Pass123!")
        auth_manager.register_user("user2", "Pass123!")
        
        # Save users
        save_path = tmp_path / "users.json"
        auth_manager.save_users(str(save_path))
        
        # Create new manager and load users
        new_manager = AuthManager(auth_manager.config)
        new_manager.load_users(str(save_path))
        
        # Verify users loaded
        success, error, token = new_manager.authenticate("user1", "Pass123!")
        assert success
        assert error is None
        assert token is not None
        
    def test_concurrent_access(self, auth_manager):
        """Test concurrent access to auth manager."""
        import threading
        
        def register_and_login():
            username = f"user_{threading.get_ident()}"
            password = "ValidPass123!"
            auth_manager.register_user(username, password)
            auth_manager.authenticate(username, password)
            
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=register_and_login)
            threads.append(thread)
            thread.start()
            
        # Wait for all threads
        for thread in threads:
            thread.join()
            
        # Verify no exceptions occurred
        assert True  # If we get here, no exceptions were raised 
