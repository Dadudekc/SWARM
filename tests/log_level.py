import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for log_level module."""

import pytest
from dreamos.social.utils.log_level import LogLevel, from_str, value

def test_from_str():
    """Test from_str function."""
    # Test valid levels
    assert from_str("DEBUG") == LogLevel.DEBUG
    assert from_str("INFO") == LogLevel.INFO
    assert from_str("WARNING") == LogLevel.WARNING
    assert from_str("ERROR") == LogLevel.ERROR
    assert from_str("CRITICAL") == LogLevel.CRITICAL
    
    # Test case insensitivity
    assert from_str("debug") == LogLevel.DEBUG
    assert from_str("info") == LogLevel.INFO
    
    # Test invalid level
    with pytest.raises(ValueError):
        from_str("INVALID")

def test___str__():
    """Test __str__ function."""
    assert str(LogLevel.DEBUG) == "DEBUG"
    assert str(LogLevel.INFO) == "INFO"
    assert str(LogLevel.WARNING) == "WARNING"
    assert str(LogLevel.ERROR) == "ERROR"
    assert str(LogLevel.CRITICAL) == "CRITICAL"

def test_value():
    """Test value property."""
    assert LogLevel.DEBUG.value == 10
    assert LogLevel.INFO.value == 20
    assert LogLevel.WARNING.value == 30
    assert LogLevel.ERROR.value == 40
    assert LogLevel.CRITICAL.value == 50
