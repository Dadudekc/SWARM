import time
import pytest
from unittest.mock import Mock, patch
from social.driver.performance_metrics import PerformanceMetrics

@pytest.fixture
def metrics():
    """Create a PerformanceMetrics instance."""
    return PerformanceMetrics()

def test_init(metrics):
    """Test initialization."""
    assert metrics.metrics == {}
    assert metrics.start_times == {}
    assert metrics.error_counts == {}

def test_start_operation(metrics):
    """Test starting an operation."""
    metrics.start_operation("test_op")
    assert "test_op" in metrics.start_times
    assert isinstance(metrics.start_times["test_op"], float)

def test_end_operation(metrics):
    """Test ending an operation."""
    metrics.start_operation("test_op")
    time.sleep(0.1)  # Simulate some operation time
    metrics.end_operation("test_op")
    
    assert "test_op" in metrics.metrics
    assert "duration" in metrics.metrics["test_op"]
    assert metrics.metrics["test_op"]["duration"] >= 0.1

def test_end_operation_without_start(metrics):
    """Test ending an operation that wasn't started."""
    with pytest.raises(KeyError):
        metrics.end_operation("test_op")

def test_record_error(metrics):
    """Test recording an error."""
    metrics.record_error("test_op", "Test error")
    
    assert "test_op" in metrics.error_counts
    assert metrics.error_counts["test_op"] == 1
    assert "errors" in metrics.metrics["test_op"]
    assert len(metrics.metrics["test_op"]["errors"]) == 1
    assert metrics.metrics["test_op"]["errors"][0]["message"] == "Test error"

def test_get_metrics(metrics):
    """Test getting metrics for an operation."""
    metrics.start_operation("test_op")
    time.sleep(0.1)
    metrics.end_operation("test_op")
    metrics.record_error("test_op", "Test error")
    
    operation_metrics = metrics.get_metrics("test_op")
    assert "duration" in operation_metrics
    assert "errors" in operation_metrics
    assert len(operation_metrics["errors"]) == 1

def test_get_metrics_nonexistent(metrics):
    """Test getting metrics for a nonexistent operation."""
    assert metrics.get_metrics("nonexistent") == {}

def test_get_all_metrics(metrics):
    """Test getting all metrics."""
    metrics.start_operation("test_op1")
    time.sleep(0.1)
    metrics.end_operation("test_op1")
    
    metrics.start_operation("test_op2")
    time.sleep(0.1)
    metrics.end_operation("test_op2")
    
    all_metrics = metrics.get_all_metrics()
    assert "test_op1" in all_metrics
    assert "test_op2" in all_metrics
    assert "duration" in all_metrics["test_op1"]
    assert "duration" in all_metrics["test_op2"]

def test_reset_metrics(metrics):
    """Test resetting metrics."""
    metrics.start_operation("test_op")
    time.sleep(0.1)
    metrics.end_operation("test_op")
    metrics.record_error("test_op", "Test error")
    
    metrics.reset_metrics()
    assert metrics.metrics == {}
    assert metrics.start_times == {}
    assert metrics.error_counts == {}

def test_get_error_count(metrics):
    """Test getting error count for an operation."""
    metrics.record_error("test_op", "Error 1")
    metrics.record_error("test_op", "Error 2")
    
    assert metrics.get_error_count("test_op") == 2

def test_get_error_count_nonexistent(metrics):
    """Test getting error count for a nonexistent operation."""
    assert metrics.get_error_count("nonexistent") == 0 