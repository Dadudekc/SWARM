"""
Stubborn Tests
------------
Legacy tests for core functionality that need to be reorganized.
"""

import pytest

# Mark all tests in this package as deprecated
pytestmark = pytest.mark.skip(reason="Stubborn tests are deprecated and will be reorganized in a future version.") 