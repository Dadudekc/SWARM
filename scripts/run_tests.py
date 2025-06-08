#!/usr/bin/env python3
"""
Enhanced test runner for Dream.OS with support for the new test structure.
Supports running unit tests, integration tests, and core module tests.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional, Set
import json
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.tests_dir = self.root_dir / "tests"
        self.results_dir = self.root_dir / "test_results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Test categories and their paths
        self.test_categories = {
            "unit": self.tests_dir / "unit",
            "integration": self.tests_dir / "integration",
            "core": {
                "messaging": self.tests_dir / "core" / "messaging",
                "utils": self.tests_dir / "core" / "utils",
                "security": self.tests_dir / "core" / "security"
            }
        }
        
        # Coverage thresholds
        self.coverage_thresholds = {
            "core": 90,
            "integration": 80,
            "unit": 95
        }

    def run_tests(
        self,
        paths: List[Path],
        verbose: bool = False,
        coverage: bool = False,
        parallel: bool = False,
        ci_mode: bool = False,
        tags: Optional[Set[str]] = None,
        notags: Optional[Set[str]] = None
    ) -> bool:
        """Run tests in the specified paths."""
        if not paths:
            print("⚠️ No test paths specified")
            return False

        # Build pytest command
        cmd = ["pytest"]
        
        # Add paths
        cmd.extend(str(p) for p in paths)
        
        # Add options
        if verbose:
            cmd.append("-v")
        
        # Handle coverage
        if coverage:
            cmd.extend(["--cov", "dreamos", "--cov-report", "term-missing"])
            if ci_mode:
                # Add coverage thresholds based on category
                for path in paths:
                    category = self._get_category_from_path(path)
                    if category in self.coverage_thresholds:
                        cmd.extend([
                            "--cov-fail-under",
                            str(self.coverage_thresholds[category])
                        ])
                        break
        
        # Handle parallel execution
        if parallel:
            cmd.extend(["-n", "auto"])
        
        # Handle tags
        if tags:
            cmd.extend(["-m", " or ".join(tags)])
        if notags:
            cmd.extend(["-m", f"not ({' or '.join(notags)})"])
        
        # CI mode settings
        if ci_mode:
            cmd.extend([
                "--strict-markers",  # Fail on unknown markers
                "--durations=10",    # Show slowest tests
                "--tb=short",        # Shorter tracebacks
                "-W", "error",       # Treat warnings as errors
                "--junitxml", str(self.results_dir / "junit.xml")  # JUnit report
            ])
        
        # Add common options
        cmd.extend([
            "--tb=short",
            "--strict-markers",
            "--durations=10"
        ])
        
        # Run tests
        print(f"🚀 Running tests: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"test_results_{timestamp}.json"
        
        results = {
            "timestamp": timestamp,
            "command": cmd,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "paths": [str(p) for p in paths],
            "tags": list(tags) if tags else None,
            "notags": list(notags) if notags else None,
            "ci_mode": ci_mode
        }
        
        with open(result_file, "w") as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("\n📊 Test Results Summary:")
        print(f"Return code: {result.returncode}")
        print(f"Results saved to: {result_file}")
        
        if result.stdout:
            print("\nOutput:")
            print(result.stdout)
        
        if result.stderr:
            print("\nErrors:")
            print(result.stderr)
        
        return result.returncode == 0

    def _get_category_from_path(self, path: Path) -> Optional[str]:
        """Determine the category from a test path."""
        path_str = str(path)
        if "unit" in path_str:
            return "unit"
        elif "integration" in path_str:
            return "integration"
        elif "core" in path_str:
            return "core"
        return None

    def get_test_paths(
        self,
        category: Optional[str] = None,
        module: Optional[str] = None
    ) -> List[Path]:
        """Get test paths based on category and module."""
        paths = []
        
        if category == "unit":
            paths.append(self.test_categories["unit"])
        elif category == "integration":
            paths.append(self.test_categories["integration"])
        elif category == "core":
            if module:
                if module in self.test_categories["core"]:
                    paths.append(self.test_categories["core"][module])
            else:
                for module_path in self.test_categories["core"].values():
                    paths.append(module_path)
        else:
            # No category specified, run all tests
            paths.append(self.tests_dir)
        
        return paths

def main():
    parser = argparse.ArgumentParser(description="Run Dream.OS tests")
    parser.add_argument(
        "--category",
        choices=["unit", "integration", "core"],
        help="Test category to run"
    )
    parser.add_argument(
        "--module",
        choices=["messaging", "utils", "security"],
        help="Core module to test (only valid with --category core)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report"
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run tests in parallel"
    )
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Run in CI mode (strict checks, coverage thresholds)"
    )
    parser.add_argument(
        "--tag",
        action="append",
        help="Run tests with specific tags (can be used multiple times)"
    )
    parser.add_argument(
        "--notag",
        action="append",
        help="Exclude tests with specific tags (can be used multiple times)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.module and args.category != "core":
        parser.error("--module can only be used with --category core")
    
    runner = TestRunner()
    paths = runner.get_test_paths(args.category, args.module)
    
    success = runner.run_tests(
        paths,
        verbose=args.verbose,
        coverage=args.coverage,
        parallel=args.parallel,
        ci_mode=args.ci,
        tags=set(args.tag) if args.tag else None,
        notags=set(args.notag) if args.notag else None
    )
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 