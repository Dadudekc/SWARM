import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""Tests for json_ops module."""

import pytest
from dreamos.core.io.json_ops import read_json, write_json

# Fixtures
@pytest.fixture
def sample_data():
    return {}

@pytest.mark.skip(reason='Pending implementation')
def test_read_json(sample_data):
    """Test read_json function."""
    # TODO: Implement test
    pass

@pytest.mark.skip(reason='Pending implementation')
def test_write_json(sample_data):
    """Test write_json function."""
    # TODO: Implement test
    pass
