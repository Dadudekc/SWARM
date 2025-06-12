import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for processor module."""

import pytest
from dreamos.core.bridge.base.processor import BridgeProcessor

# Fixtures
@pytest.fixture
def processor():
    return BridgeProcessor()

@pytest.fixture
def sample_data():
    return {}

def test_processor_initialization(processor):
    """Test processor initialization."""
    assert processor is not None
    assert processor.total_processed == 0
    assert processor.total_failed == 0

def test_update_metrics(processor):
    """Test metrics update."""
    # Test successful update
    processor._update_metrics(True)
    assert processor.total_processed == 1
    assert processor.total_failed == 0
    
    # Test failed update
    error = ValueError("Test error")
    processor._update_metrics(False, error)
    assert processor.total_processed == 1
    assert processor.total_failed == 1
