import pytest
import sys
import os
import time

def run_test(test_path, test_name=None):
    """Run a specific test with proper cleanup and timeout."""
    # Clear any existing test cache
    pytest.main(['--cache-clear'])
    
    # Build test path
    if test_name:
        test_path = f"{test_path}::{test_name}"
    
    # Run test with timeout and short traceback
    result = pytest.main([
        test_path,
        '-v',
        '--tb=short',
        '--timeout=30',
        '-xvs'
    ])
    
    return result

if __name__ == '__main__':

    # Get test path from command line or default to the full test suite
    test_path = sys.argv[1] if len(sys.argv) > 1 else 'tests'
    test_name = sys.argv[2] if len(sys.argv) > 2 else None

    # Run the tests and exit with the result code
    result = run_test(test_path, test_name)
    sys.exit(result)
