"""Tests for base metrics functionality."""

import pytest
from pathlib import Path
from dreamos.core.metrics import BaseMetrics

@pytest.fixture
def metrics():
    """Create a test metrics instance."""
    return BaseMetrics("test_metrics", Path("test_metrics"))

def test_metrics_initialization(metrics):
    """Test metrics initialization."""
    assert metrics.name == "test_metrics"
    assert metrics._counters == {}
    assert metrics._gauges == {}
    assert metrics._histograms == {}

def test_increment_counter(metrics):
    """Test counter increment."""
    metrics.increment("test_counter")
    assert metrics._counters["test_counter"] == 1
    
    metrics.increment("test_counter", 2)
    assert metrics._counters["test_counter"] == 3

def test_increment_with_tags(metrics):
    """Test counter increment with tags."""
    metrics.increment("test_counter", tags={"tag1": "value1"})
    assert metrics._counters["test_counter{tag1=value1}"] == 1

def test_gauge(metrics):
    """Test gauge setting."""
    metrics.gauge("test_gauge", 42.0)
    assert metrics._gauges["test_gauge"] == 42.0
    
    metrics.gauge("test_gauge", 100.0)
    assert metrics._gauges["test_gauge"] == 100.0

def test_histogram(metrics):
    """Test histogram recording."""
    metrics.histogram("test_hist", 1.0)
    metrics.histogram("test_hist", 2.0)
    metrics.histogram("test_hist", 3.0)
    
    assert len(metrics._histograms["test_hist"]) == 3
    assert metrics._histograms["test_hist"] == [1.0, 2.0, 3.0]

def test_get_metrics(metrics):
    """Test getting all metrics."""
    metrics.increment("test_counter")
    metrics.gauge("test_gauge", 42.0)
    metrics.histogram("test_hist", 1.0)
    
    result = metrics.get_metrics()
    assert result["name"] == "test_metrics"
    assert result["counters"]["test_counter"] == 1
    assert result["gauges"]["test_gauge"] == 42.0
    assert "test_hist" in result["histograms"]
    assert result["histograms"]["test_hist"]["count"] == 1
    assert result["histograms"]["test_hist"]["sum"] == 1.0

def test_reset(metrics):
    """Test metrics reset."""
    metrics.increment("test_counter")
    metrics.gauge("test_gauge", 42.0)
    metrics.histogram("test_hist", 1.0)
    
    metrics.reset()
    assert metrics._counters == {}
    assert metrics._gauges == {}
    assert metrics._histograms == {} 