"""
Unit tests for the IdentityUtils module.
"""

import pytest
from datetime import datetime
from dreamos.core.security.identity_utils import IdentityUtils

@pytest.fixture
def identity_config():
    """Fixture providing test identity configuration."""
    return {
        'min_password_length': 8,
        'require_special_chars': True,
        'password_history_size': 5
    }

class TestIdentityUtils:
    """Test suite for IdentityUtils class."""
    
    def test_generate_agent_id(self):
        """Test agent ID generation."""
        # Test default prefix
        agent_id = IdentityUtils.generate_agent_id()
        assert agent_id.startswith("agent-")
        assert len(agent_id.split("-")) == 3
        
        # Test custom prefix
        custom_id = IdentityUtils.generate_agent_id("test")
        assert custom_id.startswith("test-")
        
        # Test uniqueness
        ids = {IdentityUtils.generate_agent_id() for _ in range(100)}
        assert len(ids) == 100
        
    @pytest.mark.parametrize("password,expected_valid,expected_error", [
        ("short", False, "Password must be at least 8 characters"),
        ("no_special", False, "Password must contain at least one special character"),
        ("no_upper", False, "Password must contain at least one uppercase letter"),
        ("no_lower", False, "Password must contain at least one lowercase letter"),
        ("no_numbers", False, "Password must contain at least one number"),
        ("ValidPass123!", True, None),
        ("Another1@Pass", True, None),
    ])
    def test_validate_password(self, identity_config, password, expected_valid, expected_error):
        """Test password validation with various inputs."""
        is_valid, error = IdentityUtils.validate_password(password, identity_config)
        assert is_valid == expected_valid
        if not expected_valid:
            assert error == expected_error
            
    def test_password_hashing(self):
        """Test password hashing and verification."""
        password = "TestPass123!"
        
        # Test new hash generation
        hash1, salt1 = IdentityUtils.hash_password(password)
        assert hash1 != password
        assert len(salt1) == 32  # 16 bytes in hex
        
        # Test verification
        assert IdentityUtils.verify_password(password, hash1, salt1)
        assert not IdentityUtils.verify_password("WrongPass123!", hash1, salt1)
        
        # Test with provided salt
        hash2, salt2 = IdentityUtils.hash_password(password, salt1)
        assert hash2 == hash1  # Same salt should produce same hash
        
    def test_generate_token(self):
        """Test token generation."""
        # Test default length
        token = IdentityUtils.generate_token()
        assert len(token) == 64  # 32 bytes in hex
        
        # Test custom length
        short_token = IdentityUtils.generate_token(16)
        assert len(short_token) == 32  # 16 bytes in hex
        
        # Test uniqueness
        tokens = {IdentityUtils.generate_token() for _ in range(100)}
        assert len(tokens) == 100
        
    @pytest.mark.parametrize("name,expected", [
        ("test agent", "Test Agent"),
        ("TEST-AGENT", "Test Agent"),
        ("test@agent#123", "Test Agent 123"),
        ("  extra  spaces  ", "Extra Spaces"),
        ("mixed-CASE-Name", "Mixed Case Name"),
    ])
    def test_format_agent_name(self, name, expected):
        """Test agent name formatting."""
        assert IdentityUtils.format_agent_name(name) == expected 