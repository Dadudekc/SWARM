import pytest
import sys
import shutil
from pathlib import Path


def run_test(test_path="tests", test_name=None):
    """Run tests with a timeout and short traceback."""
    cache_dir = Path(".pytest_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    if test_name:
        test_path = f"{test_path}::{test_name}"

    return pytest.main([
        test_path,
        "-v",
        "--tb=short",
        "--timeout=30",
        "-xvs"
    ])


if __name__ == "__main__":
    # Get test path and name from CLI args if provided
    test_path = sys.argv[1] if len(sys.argv) > 1 else "tests"
    test_name = sys.argv[2] if len(sys.argv) > 2 else None

    result = run_test(test_path, test_name)
    sys.exit(result)
