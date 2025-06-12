"""Tests for file metrics functionality."""

import pytest
from pathlib import Path
from dreamos.core.metrics import FileMetrics

@pytest.fixture
def file_metrics():
    """Create a test file metrics instance."""
    return FileMetrics(Path("test_metrics"))

def test_file_metrics_initialization(file_metrics):
    """Test file metrics initialization."""
    assert file_metrics.name == "file_metrics"

def test_record_read(file_metrics):
    """Test recording a file read."""
    file_metrics.record_read("test.txt", 1024, "utf-8")
    assert file_metrics._counters["file_reads{path=" + str(Path("test.txt").resolve()) + ",encoding=utf-8}"] == 1
    assert file_metrics._histograms["file_read_bytes"] == [1024]

def test_record_write(file_metrics):
    """Test recording a file write."""
    file_metrics.record_write("test.txt", 2048, "utf-8")
    assert file_metrics._counters["file_writes{path=" + str(Path("test.txt").resolve()) + ",encoding=utf-8}"] == 1
    assert file_metrics._histograms["file_write_bytes"] == [2048]

def test_record_error(file_metrics):
    """Test recording a file error."""
    file_metrics.record_error("test.txt", "read", "Permission denied")
    assert file_metrics._counters["file_errors{path=" + str(Path("test.txt").resolve()) + ",operation=read}"] == 1

def test_record_directory_operation(file_metrics):
    """Test recording a directory operation."""
    file_metrics.record_directory_operation("test_dir", "create")
    assert file_metrics._counters["directory_operations{path=" + str(Path("test_dir").resolve()) + ",operation=create}"] == 1

def test_get_metrics(file_metrics):
    """Test getting file metrics."""
    file_metrics.record_read("test.txt", 1024)
    file_metrics.record_write("test.txt", 2048)
    file_metrics.record_error("test.txt", "read", "Permission denied")
    file_metrics.record_directory_operation("test_dir", "create")
    
    result = file_metrics.get_metrics()
    assert result["name"] == "file_metrics"
    assert "file_reads" in result["counters"]
    assert "file_writes" in result["counters"]
    assert "file_errors" in result["counters"]
    assert "directory_operations" in result["counters"]
    assert "file_read_bytes" in result["histograms"]
    assert "file_write_bytes" in result["histograms"] 