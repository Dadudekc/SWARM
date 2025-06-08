"""
Tests for token handling implementation.
"""

import pytest
import time
from datetime import datetime, timedelta
from dreamos.core.auth.token import TokenInfo, TokenHandler

def test_token_info_creation():
    """Test token info creation and basic properties."""
    now = datetime.now()
    token_info = TokenInfo(
        user_id="test_user",
        created_at=now,
        expires_at=now + timedelta(hours=1)
    )
    
    assert token_info.user_id == "test_user"
    assert token_info.is_valid
    assert token_info.time_remaining > 0
    assert isinstance(token_info.data, dict)

def test_token_info_expiration():
    """Test token info expiration handling."""
    now = datetime.now()
    token_info = TokenInfo(
        user_id="test_user",
        created_at=now,
        expires_at=now + timedelta(seconds=1)
    )
    
    assert token_info.is_valid
    time.sleep(1.1)  # Wait for expiration
    assert not token_info.is_valid
    assert token_info.time_remaining == 0

def test_token_handler_initialization():
    """Test token handler initialization."""
    handler = TokenHandler()
    assert handler.default_ttl == 3600
    assert handler.min_token_length == 32
    assert len(handler.secret_key) == 64  # 32 bytes in hex

def test_token_generation():
    """Test token generation."""
    handler = TokenHandler()
    token = handler.generate_token("test_user")
    
    assert len(token) >= handler.min_token_length
    assert handler.validate_token(token)
    
    token_info = handler.get_token_info(token)
    assert token_info.user_id == "test_user"
    assert token_info.is_valid

def test_token_validation():
    """Test token validation."""
    handler = TokenHandler()
    token = handler.generate_token("test_user")
    
    assert handler.validate_token(token)
    assert not handler.validate_token("invalid_token")

def test_token_refresh():
    """Test token refresh."""
    handler = TokenHandler()
    token = handler.generate_token("test_user")
    
    new_token = handler.refresh_token(token)
    assert new_token is not None
    assert new_token != token
    assert not handler.validate_token(token)  # Old token invalidated
    assert handler.validate_token(new_token)  # New token valid

def test_token_invalidation():
    """Test token invalidation."""
    handler = TokenHandler()
    token = handler.generate_token("test_user")
    
    assert handler.invalidate_token(token)
    assert not handler.validate_token(token)
    assert not handler.invalidate_token("invalid_token")

def test_token_cleanup():
    """Test expired token cleanup."""
    handler = TokenHandler()
    now = datetime.now()
    
    # Create an expired token
    token_info = TokenInfo(
        user_id="test_user",
        created_at=now - timedelta(hours=2),
        expires_at=now - timedelta(hours=1)
    )
    token = "expired_token"
    handler._tokens[token] = token_info
    
    # Create a valid token
    valid_token = handler.generate_token("valid_user")
    
    # Run cleanup
    cleaned = handler.cleanup_expired()
    assert cleaned == 1
    assert not handler.validate_token(token)
    assert handler.validate_token(valid_token)

def test_token_custom_ttl():
    """Test token generation with custom TTL."""
    handler = TokenHandler()
    token = handler.generate_token("test_user", ttl=2)
    
    assert handler.validate_token(token)
    time.sleep(2.1)  # Wait for expiration
    assert not handler.validate_token(token)

def test_token_custom_scope():
    """Test token generation with custom scope."""
    handler = TokenHandler()
    token = handler.generate_token("test_user", scope="admin")
    
    token_info = handler.get_token_info(token)
    assert token_info.scope == "admin"

def test_token_custom_data():
    """Test token generation with custom data."""
    handler = TokenHandler()
    custom_data = {"role": "admin", "permissions": ["read", "write"]}
    token = handler.generate_token("test_user", data=custom_data)
    
    token_info = handler.get_token_info(token)
    assert token_info.data == custom_data 
