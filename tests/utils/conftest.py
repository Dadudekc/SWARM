"""Pytest configuration for utils tests."""

import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def tmp_file(tmp_path):
    """Create a temporary file for testing."""
    return tmp_path / "test.txt"

@pytest.fixture
def tmp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path / "test_dir"

@pytest.fixture
def tmp_json(tmp_path):
    """Create a temporary JSON file for testing."""
    return tmp_path / "test.json"

@pytest.fixture
def tmp_yaml(tmp_path):
    """Create a temporary YAML file for testing."""
    return tmp_path / "test.yaml" 