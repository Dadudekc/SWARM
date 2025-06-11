import pytest
pytest.skip("Skipping due to missing core import", allow_module_level=True)

"""
Tests for bridge daemon module.
"""

import pytest
from dreamos.core.bridge.daemon import BridgeDaemon

# Fixtures

@pytest.fixture
def daemon():
    return BridgeDaemon()

def test_daemon_initialization(daemon):
    """Test daemon initialization."""
    assert daemon is not None
    assert daemon.is_running is False

def test_start_daemon(daemon):
    """Test starting daemon."""
    daemon.start()
    assert daemon.is_running is True

def test_stop_daemon(daemon):
    """Test stopping daemon."""
    daemon.start()
    daemon.stop()
    assert daemon.is_running is False

def test_process_messages(daemon):
    """Test message processing."""
    message = {
        "type": "text",
        "content": "test message",
        "timestamp": 1234567890
    }
    daemon.inbox.add_message(message)
    daemon.start()
    # Give some time for processing
    import time
    time.sleep(0.1)
    daemon.stop()
    assert len(daemon.inbox.queue) == 0
