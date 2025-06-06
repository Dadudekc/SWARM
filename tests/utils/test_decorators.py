"""
Test decorators for platform-specific and feature-specific tests.
"""

import pytest
import platform
import os

def platform_marker(platform_name):
    """Decorator to mark tests for specific platforms."""
    return pytest.mark.skipif(
        platform.system().lower() != platform_name.lower(),
        reason=f"Test only runs on {platform_name}"
    )

def skip_if_linux(func):
    """Skip test on Linux."""
    return platform_marker("linux")(func)

def skip_if_windows(func):
    """Skip test on Windows."""
    return platform_marker("windows")(func)

def skip_if_mac(func):
    """Skip test on macOS."""
    return platform_marker("darwin")(func)

def requires_gui(func):
    """Skip test if GUI is not available."""
    return pytest.mark.skipif(
        not os.environ.get("DISPLAY") and platform.system() != "Windows",
        reason="GUI not available"
    )(func)

def swarm_core(func):
    """Mark test as part of swarm core functionality."""
    return pytest.mark.swarm_core(func)

def bridge_integration(func):
    """Mark test as part of bridge integration."""
    return pytest.mark.bridge_integration(func)

def cellphone_pipeline(func):
    """Mark test as part of cellphone pipeline."""
    return pytest.mark.cellphone_pipeline(func)

def pyqt5_test(func):
    """Mark test as requiring PyQt5."""
    return pytest.mark.pyqt5(func) 