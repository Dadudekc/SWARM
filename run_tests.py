"""
Run Tests
--------
Script to run the overnight test runner using Python's exec function.
"""

import os
import sys
from pathlib import Path

def main():
    """Main entry point."""
    # Get the path to the overnight test runner script
    script_path = Path(__file__).parent / "scripts" / "overnight_test_runner.py"
    
    # Read the script content
    with open(script_path) as f:
        script_content = f.read()
    
    # Execute the script
    exec(script_content, {"__name__": "__main__"})

if __name__ == "__main__":
    main()
