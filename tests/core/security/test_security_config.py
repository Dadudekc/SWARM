"""
Unit tests for the SecurityConfig module.
"""

import pytest
import json
import os
from pathlib import Path
from dreamos.core.security.security_config import SecurityConfig

@pytest.fixture
def temp_config_dir(tmp_path):
    """Fixture providing a temporary config directory."""
    return tmp_path

@pytest.fixture
def security_config(temp_config_dir):
    """Fixture providing a SecurityConfig instance with custom path."""
    config_path = temp_config_dir / "security_config.json"
    return SecurityConfig(str(config_path))

class TestSecurityConfig:
    """Test suite for SecurityConfig class."""
    
    def test_default_config(self, security_config):
        """Test default configuration values."""
        # Check auth config
        auth_config = security_config.get_auth_config()
        assert 'token_expiry' in auth_config
        assert 'refresh_token_expiry' in auth_config
        assert 'max_login_attempts' in auth_config
        assert 'lockout_duration' in auth_config
        
        # Check session config
        session_config = security_config.get_session_config()
        assert 'max_sessions_per_user' in session_config
        assert 'session_timeout' in session_config
        assert 'cleanup_interval' in session_config
        
        # Check identity config
        identity_config = security_config.get_identity_config()
        assert 'min_password_length' in identity_config
        assert 'require_special_chars' in identity_config
        assert 'password_history_size' in identity_config
        
    def test_config_persistence(self, security_config, temp_config_dir):
        """Test configuration persistence to disk."""
        # Update some values
        security_config.update_config('auth', {
            'token_expiry': 7200,  # 2 hours
            'max_login_attempts': 10
        })
        
        # Create new instance with same path
        new_config = SecurityConfig(str(temp_config_dir / "security_config.json"))
        
        # Verify values persisted
        auth_config = new_config.get_auth_config()
        assert auth_config['token_expiry'] == 7200
        assert auth_config['max_login_attempts'] == 10
        
    def test_config_validation(self, security_config):
        """Test configuration validation and merging."""
        # Update with partial config
        security_config.update_config('auth', {
            'token_expiry': 3600
        })
        
        # Verify other values unchanged
        auth_config = security_config.get_auth_config()
        assert auth_config['token_expiry'] == 3600
        assert 'refresh_token_expiry' in auth_config
        assert 'max_login_attempts' in auth_config
        
    def test_invalid_section(self, security_config):
        """Test handling of invalid configuration section."""
        with pytest.raises(ValueError):
            security_config.update_config('invalid_section', {'key': 'value'})
            
    def test_config_file_corruption(self, security_config, temp_config_dir):
        """Test handling of corrupted configuration file."""
        config_path = temp_config_dir / "security_config.json"
        
        # Write invalid JSON
        with open(config_path, 'w') as f:
            f.write("invalid json")
            
        # Create new instance - should use defaults
        new_config = SecurityConfig(str(config_path))
        assert new_config.get_auth_config() == SecurityConfig.DEFAULT_CONFIG['auth']
        
    def test_config_file_permissions(self, security_config, temp_config_dir):
        """Test handling of file permission issues."""
        config_path = temp_config_dir / "security_config.json"
        
        # Make file read-only
        os.chmod(config_path, 0o444)
        
        # Try to update config
        with pytest.raises(IOError):
            security_config.update_config('auth', {'token_expiry': 3600})
            
    def test_config_section_updates(self, security_config):
        """Test updating individual configuration sections."""
        # Update auth section
        security_config.update_config('auth', {
            'token_expiry': 3600,
            'max_login_attempts': 5
        })
        
        # Update session section
        security_config.update_config('session', {
            'session_timeout': 1800,
            'cleanup_interval': 300
        })
        
        # Update identity section
        security_config.update_config('identity', {
            'min_password_length': 12,
            'require_special_chars': False
        })
        
        # Verify updates
        assert security_config.get_auth_config()['token_expiry'] == 3600
        assert security_config.get_session_config()['session_timeout'] == 1800
        assert security_config.get_identity_config()['min_password_length'] == 12
        
    def test_config_reload(self, security_config, temp_config_dir):
        """Test reloading configuration from disk."""
        # Update config
        security_config.update_config('auth', {'token_expiry': 3600})
        
        # Manually modify file
        config_path = temp_config_dir / "security_config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        config['auth']['token_expiry'] = 7200
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
            
        # Create new instance - should load modified values
        new_config = SecurityConfig(str(config_path))
        assert new_config.get_auth_config()['token_expiry'] == 7200 