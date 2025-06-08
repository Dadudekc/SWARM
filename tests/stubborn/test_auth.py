"""
Tests for the authentication system after migration.
"""

import pytest
from pathlib import Path
import sys
import importlib

# Add dreamos to path for testing
sys.path.append(str(Path(__file__).parent.parent.parent))

def test_auth_module_imports():
    """Test that auth module can be imported from new location."""
    try:
        from dreamos.core.auth import token, base, interface, retry
        assert token is not None
        assert base is not None
        assert interface is not None
        assert retry is not None
    except ImportError as e:
        pytest.fail(f"Failed to import auth modules: {e}")

def test_auth_files_exist():
    """Test that all auth files exist in new location."""
    auth_dir = Path(__file__).parent.parent.parent / 'dreamos' / 'core' / 'auth'
    required_files = ['token.py', 'base.py', '__init__.py', 
                     'retry.py', 'interface.py']
    
    for file in required_files:
        assert (auth_dir / file).exists(), f"Missing file: {file}"

def test_auth_functionality():
    """Test basic auth functionality."""
    from dreamos.core.auth import token
    
    # Test token creation
    token_handler = token.TokenHandler()
    test_token = token_handler.generate_token("test_user")
    assert test_token is not None
    assert token_handler.validate_token(test_token)

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
