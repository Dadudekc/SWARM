"""Tests for the log metrics functionality."""

import pytest
from datetime import datetime
from dreamos.core.monitoring.metrics import LogMetrics

@pytest.fixture
def metrics():
    """Create a fresh metrics instance for each test."""
    return LogMetrics()

def test_metrics_initialization(metrics):
    """Test metrics initialization."""
    assert metrics.total_logs == 0
    assert metrics.total_bytes == 0
    assert metrics.error_count == 0
    assert metrics.last_error is None
    assert metrics.last_error_message is None
    assert metrics.last_rotation is None
    assert len(metrics.platform_counts) == 0
    assert len(metrics.level_counts) == 0
    assert len(metrics.status_counts) == 0
    assert len(metrics.format_counts) == 0

def test_metrics_increment_logs(metrics):
    """Test incrementing log counts."""
    metrics.increment_logs(
        platform="test",
        level="INFO",
        status="success",
        format_type="json",
        bytes_written=100
    )
    
    assert metrics.total_logs == 1
    assert metrics.total_bytes == 100
    assert metrics.platform_counts["test"] == 1
    assert metrics.level_counts["INFO"] == 1
    assert metrics.status_counts["success"] == 1
    assert metrics.format_counts["json"] == 1

def test_metrics_record_error(metrics):
    """Test recording errors."""
    error_message = "Test error"
    metrics.record_error(error_message)
    
    assert metrics.error_count == 1
    assert metrics.last_error is not None
    assert metrics.last_error_message == error_message
    assert isinstance(metrics.last_error, datetime)

def test_metrics_record_rotation(metrics):
    """Test recording rotations."""
    metrics.record_rotation()
    
    assert metrics.last_rotation is not None
    assert isinstance(metrics.last_rotation, datetime)

def test_metrics_reset(metrics):
    """Test resetting metrics."""
    # Add some data
    metrics.increment_logs("test", "INFO", "success", "json", 100)
    metrics.record_error("test error")
    metrics.record_rotation()
    
    # Reset
    metrics.reset()
    
    # Verify reset
    assert metrics.total_logs == 0
    assert metrics.total_bytes == 0
    assert metrics.error_count == 0
    assert metrics.last_error is None
    assert metrics.last_error_message is None
    assert metrics.last_rotation is None
    assert len(metrics.platform_counts) == 0
    assert len(metrics.level_counts) == 0
    assert len(metrics.status_counts) == 0
    assert len(metrics.format_counts) == 0 