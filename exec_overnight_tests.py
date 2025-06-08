"""
Execute Overnight Tests
---------------------
Wrapper script that executes the overnight test runner using Python's exec function.
This approach allows for dynamic execution of the test runner script while maintaining
proper globals and execution context.
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

    # Execute the script with proper globals
    globals_dict = {"__name__": "__main__", "__file__": str(script_path)}
    exec(script_content, globals_dict)

if __name__ == "__main__":
    main()
