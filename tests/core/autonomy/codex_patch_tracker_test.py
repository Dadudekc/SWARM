"""
Tests for codex_patch_tracker module.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open
from dreamos.core.autonomy.codex_patch_tracker import CodexPatchTracker

# Fixtures

@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return MagicMock()

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    return tmp_path / "test_file.txt"

@pytest.fixture
def patch_tracker(tmp_path):
    """Create a CodexPatchTracker instance with temporary failure log directory."""
    with patch('dreamos.core.autonomy.codex_patch_tracker.logger') as mock_logger:
        tracker = CodexPatchTracker()
        tracker.failure_log_dir = tmp_path / "scanner_failures"
        tracker.failure_log_dir.mkdir(exist_ok=True)
        yield tracker

@pytest.fixture
def mock_scanner_success():
    """Mock successful scanner run."""
    return MagicMock(
        returncode=0,
        stdout=json.dumps({
            "total_files": 100,
            "total_duplicates": 0,
            "scan_time": "2024-03-14T12:00:00",
            "categories": {}
        })
    )

@pytest.fixture
def mock_scanner_failure():
    """Mock failed scanner run."""
    return MagicMock(
        returncode=1,
        stdout=json.dumps({
            "total_files": 100,
            "total_duplicates": 5,
            "scan_time": "2024-03-14T12:00:00",
            "categories": {
                "functions": 3,
                "classes": 2
            }
        })
    )

# Test cases

def test_init_creates_failure_log_dir(tmp_path):
    """Test that initialization creates the failure log directory."""
    with patch('pathlib.Path.mkdir') as mock_mkdir:
        tracker = CodexPatchTracker()
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

def test_validate_with_scanner_success(patch_tracker, mock_scanner_success):
    """Test successful scanner validation."""
    with patch('subprocess.run', return_value=mock_scanner_success):
        is_valid, results = patch_tracker.validate_with_scanner("test_patch", "test_file.py")
        assert is_valid
        assert results["total_duplicates"] == 0
        assert not (patch_tracker.failure_log_dir / "test_patch.json").exists()

def test_validate_with_scanner_failure(patch_tracker, mock_scanner_failure):
    """Test failed scanner validation."""
    with patch('subprocess.run', return_value=mock_scanner_failure):
        is_valid, results = patch_tracker.validate_with_scanner("test_patch", "test_file.py")
        assert not is_valid
        assert results["total_duplicates"] == 5
        assert (patch_tracker.failure_log_dir / "test_patch.json").exists()

def test_validate_with_scanner_error(patch_tracker):
    """Test scanner validation with execution error."""
    with patch('subprocess.run', side_effect=Exception("Scanner error")):
        is_valid, results = patch_tracker.validate_with_scanner("test_patch", "test_file.py")
        assert not is_valid
        assert "error" in results

def test_track_patch_with_scanner_success(patch_tracker, mock_scanner_success):
    """Test tracking a patch that passes scanner validation."""
    with patch('subprocess.run', return_value=mock_scanner_success):
        patch_tracker.track_patch("test_patch", "test_file.py", "success")
        patch_info = patch_tracker.get_patch_status("test_patch")
        assert patch_info["outcome"] == "success"
        assert patch_info["scanner_results"]["total_duplicates"] == 0

def test_track_patch_with_scanner_failure(patch_tracker, mock_scanner_failure):
    """Test tracking a patch that fails scanner validation."""
    with patch('subprocess.run', return_value=mock_scanner_failure):
        patch_tracker.track_patch("test_patch", "test_file.py", "success")
        patch_info = patch_tracker.get_patch_status("test_patch")
        assert patch_info["outcome"] == "scanner_failed"
        assert patch_info["scanner_results"]["total_duplicates"] == 5

def test_get_all_patches_includes_scanner_results(patch_tracker, mock_scanner_success):
    """Test that get_all_patches includes scanner results."""
    with patch('subprocess.run', return_value=mock_scanner_success):
        patch_tracker.track_patch("test_patch", "test_file.py", "success")
        all_patches = patch_tracker.get_all_patches()
        assert "test_patch" in all_patches
        assert "scanner_results" in all_patches["test_patch"]
