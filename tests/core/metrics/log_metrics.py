"""Tests for log metrics functionality."""

import pytest
from pathlib import Path
from dreamos.core.metrics import LogMetrics

@pytest.fixture
def log_metrics():
    """Create a test log metrics instance."""
    return LogMetrics(Path("test_metrics"))

def test_log_metrics_initialization(log_metrics):
    """Test log metrics initialization."""
    assert log_metrics.name == "log_metrics"
    assert log_metrics.last_error is None
    assert log_metrics.last_error_message is None
    assert log_metrics.last_rotation is None

def test_record_log(log_metrics):
    """Test recording a log entry."""
    log_metrics.record_log("INFO", "discord", "success")
    assert log_metrics._counters["log_entries{level=info,platform=discord,status=success}"] == 1

def test_record_error(log_metrics):
    """Test recording a log error."""
    log_metrics.record_error("Test error")
    assert log_metrics._counters["log_errors"] == 1
    assert log_metrics.last_error is not None
    assert log_metrics.last_error_message == "Test error"

def test_record_rotation(log_metrics):
    """Test recording a log rotation."""
    log_metrics.record_rotation()
    assert log_metrics._counters["log_rotations"] == 1
    assert log_metrics.last_rotation is not None

def test_get_metrics(log_metrics):
    """Test getting log metrics."""
    log_metrics.record_log("INFO", "discord", "success")
    log_metrics.record_error("Test error")
    log_metrics.record_rotation()
    
    result = log_metrics.get_metrics()
    assert result["name"] == "log_metrics"
    assert "log_entries{level=info,platform=discord,status=success}" in result["counters"]
    assert result["counters"]["log_errors"] == 1
    assert result["counters"]["log_rotations"] == 1
    assert result["last_error"] is not None
    assert result["last_error_message"] == "Test error"
    assert result["last_rotation"] is not None 