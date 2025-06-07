import pytest
import sys
import shutil
from pathlib import Path


def run_test(test_path="tests", test_name=None, exclude_patterns=None):
    """Run tests with a timeout and short traceback.
    
    Args:
        test_path: Path to test directory or file
        test_name: Specific test to run
        exclude_patterns: List of patterns to exclude (e.g. ['voice', 'discord'])
    """
    cache_dir = Path(".pytest_cache")
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    if test_name:
        test_path = f"{test_path}::{test_name}"

    # Build pytest args
    pytest_args = [
        test_path,
        "-v",
        "--tb=short",
        "--timeout=30",
        "-xvs"
    ]
    
    # Add exclusions if provided
    if exclude_patterns:
        exclude_expr = " and ".join(f"not {pattern}" for pattern in exclude_patterns)
        pytest_args.extend(["-k", exclude_expr])

    return pytest.main(pytest_args)


if __name__ == "__main__":
    # Default exclusions for problematic tests
    default_exclusions = ["voice", "discord", "dreamscribe"]
    
    # Prefer specific test path if not provided
    test_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else 'tests'
    )
    test_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Allow overriding exclusions via command line
    exclude_patterns = sys.argv[3:] if len(sys.argv) > 3 else default_exclusions

    result = run_test(test_path, test_name, exclude_patterns)
    sys.exit(result)
