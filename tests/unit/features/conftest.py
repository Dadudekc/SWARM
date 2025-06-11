"""
UI Test Configuration
-------------------
Shared fixtures and configuration for UI tests.
"""

import pytest
from pytestqt.qtbot import QtBot
from dreamos.core.ui import MainWindow

@pytest.fixture
def main_window(qtbot):
    """Create a MainWindow instance for testing.
    
    Args:
        qtbot: pytest-qt fixture for Qt testing
        
    Returns:
        MainWindow instance
    """
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    yield window
    window.close()

@pytest.fixture
def auto_close_timer(qtbot):
    """Create a timer that closes windows after a delay.
    
    Args:
        qtbot: pytest-qt fixture for Qt testing
        
    Returns:
        Function that creates and starts a close timer
    """
    def _create_timer(window, delay=100):
        timer = qtbot.waitExposed(window, timeout=delay)
        window.close()
        return timer
    return _create_timer 