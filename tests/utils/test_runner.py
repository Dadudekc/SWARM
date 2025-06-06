#!/usr/bin/env python3
"""Safe test runner that excludes known problematic tests."""

import os
import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run tests with safe exclusions."""
    # Get the project root directory
    project_root = Path(__file__).resolve().parent.parent.parent  # Go up to project root
    
    # Build the test command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-k", "not voice and not discord and not dreamscribe"
    ]
    
    # Run the tests
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests()) 