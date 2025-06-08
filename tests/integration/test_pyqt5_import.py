#!/usr/bin/env python3
"""Test PyQt5 imports."""

import sys
import os
import pytest
pytestmark = pytest.mark.pyqt5

def test_pyqt5_import():
    """Test PyQt5 imports and print results."""
    try:
        import PyQt5
        from PyQt5.QtCore import Qt
        print("✅ PyQt5 import successful")
        print(f"Python path: {sys.path}")
        print(f"PyQt5 location: {os.path.dirname(PyQt5.__file__)}")
    except ImportError as e:
        print(f"❌ PyQt5 import failed: {e}")
        print(f"Python path: {sys.path}")
        print(f"Current directory: {os.getcwd()}")

if __name__ == "__main__":
    test_pyqt5_import() 
