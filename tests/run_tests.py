"""
Test runner for Discord bot tests.
"""

import os
import sys
import pytest
from datetime import datetime
from pathlib import Path

def run_tests():
    """Run all tests with proper reporting."""
    # Get test directory
    test_dir = Path(__file__).parent
    
    # Create reports directory
    reports_dir = test_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # Generate report filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = reports_dir / f"test_report_{timestamp}.html"
    
    # Run tests with coverage and HTML report
    args = [
        "--verbose",
        "--cov=social",
        "--cov-report=term-missing",
        f"--html={report_file}",
        "--self-contained-html",
        str(test_dir)
    ]
    
    # Run pytest
    result = pytest.main(args)
    
    # Print summary
    print("\nTest Summary:")
    print(f"Report saved to: {report_file}")
    print(f"Exit code: {result}")
    
    return result

if __name__ == "__main__":
    sys.exit(run_tests()) 