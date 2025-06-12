"""Tests for bridge metrics functionality."""

import pytest
from pathlib import Path
from dreamos.core.metrics import BridgeMetrics

@pytest.fixture
def bridge_metrics():
    """Create a test bridge metrics instance."""
    return BridgeMetrics(Path("test_metrics"))

def test_bridge_metrics_initialization(bridge_metrics):
    """Test bridge metrics initialization."""
    assert bridge_metrics.name == "bridge_metrics"
    assert bridge_metrics.last_request is None
    assert bridge_metrics.last_error is None

def test_record_request(bridge_metrics):
    """Test recording a bridge request."""
    bridge_metrics.record_request("discord", "message_send")
    assert bridge_metrics._counters["bridge_requests{bridge=discord,operation=message_send}"] == 1
    assert bridge_metrics.last_request is not None

def test_record_success(bridge_metrics):
    """Test recording a successful bridge operation."""
    bridge_metrics.record_success("discord", "message_send", 0.5)
    assert bridge_metrics._counters["bridge_successes{bridge=discord,operation=message_send}"] == 1
    assert bridge_metrics._histograms["bridge_duration{bridge=discord,operation=message_send}"] == [0.5]

def test_record_error(bridge_metrics):
    """Test recording a bridge error."""
    bridge_metrics.record_error("discord", "message_send", "Rate limit exceeded")
    assert bridge_metrics._counters["bridge_errors{bridge=discord,operation=message_send}"] == 1
    assert bridge_metrics.last_error is not None

def test_get_metrics(bridge_metrics):
    """Test getting bridge metrics."""
    bridge_metrics.record_request("discord", "message_send")
    bridge_metrics.record_success("discord", "message_send", 0.5)
    bridge_metrics.record_error("discord", "message_send", "Rate limit exceeded")
    
    result = bridge_metrics.get_metrics()
    assert result["name"] == "bridge_metrics"
    assert "bridge_requests{bridge=discord,operation=message_send}" in result["counters"]
    assert "bridge_successes{bridge=discord,operation=message_send}" in result["counters"]
    assert "bridge_errors{bridge=discord,operation=message_send}" in result["counters"]
    assert "bridge_duration{bridge=discord,operation=message_send}" in result["histograms"]
    assert result["last_request"] is not None
    assert result["last_error"] is not None 