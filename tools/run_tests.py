#!/usr/bin/env python3
"""
Test runner script for Dream.OS project.
Handles test discovery, execution, and reporting across all environments.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import json
import os
import argparse

class TestRunner:
    def __init__(self, category: str = None):
        self.root_dir = Path(__file__).parent
        self.category = category
        self.results: Dict[str, Any] = {
            "start_time": datetime.now().isoformat(),
            "tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        }
        
        # Core test files by category
        self.test_categories = {
            "core": [
                "tests/core/utils/test_core_utils.py",
                "tests/core/test_prompt_router.py",
            ],
            "messaging": [
                "tests/core/messaging/test_high_priority_dispatcher.py",
                "tests/core/messaging/test_agent_onboarder.py",
            ],
            "ui": [
                "tests/ui/test_gui.py",
            ],
            "tools": [
                "tests/agent_tools/test_agent_restarter.py",
            ]
        }
        
        # Get test files based on category
        self.test_files = []
        if category:
            if category in self.test_categories:
                self.test_files = self.test_categories[category]
            else:
                print(f"⚠️ Unknown category: {category}")
                sys.exit(1)
        else:
            # Run all tests
            for category_tests in self.test_categories.values():
                self.test_files.extend(category_tests)

    def run_test(self, test_path: str) -> Dict[str, Any]:
        """Run a single test file and return results."""
        print(f"\n🔍 Running {test_path}")
        
        # Use pytest to run the test
        cmd = [
            sys.executable,
            "-m", "pytest",
            test_path,  # Use the relative path
            "-v",
            "--capture=tee-sys"  # Capture output while still showing it
        ]
        
        # Set QT_QPA_PLATFORM=offscreen for UI tests
        env = os.environ.copy()
        if self.category == "ui":
            env["QT_QPA_PLATFORM"] = "offscreen"
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.root_dir),  # Set working directory to project root
            env=env
        )
        
        # Parse test results
        test_result = {
            "path": test_path,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "timestamp": datetime.now().isoformat()
        }
        
        # Update summary
        if result.returncode == 0:
            self.results["summary"]["passed"] += 1
        else:
            self.results["summary"]["failed"] += 1
        self.results["summary"]["total"] += 1
        
        return test_result

    def save_results(self):
        """Save test results to a JSON file."""
        self.results["end_time"] = datetime.now().isoformat()
        results_file = self.root_dir / "test_results.json"
        
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📊 Results saved to {results_file}")

    def print_summary(self):
        """Print a summary of test results."""
        print("\n" + "="*50)
        print("📊 Test Summary")
        print("="*50)
        if self.category:
            print(f"Category: {self.category}")
        print(f"Total Tests: {self.results['summary']['total']}")
        print(f"✅ Passed: {self.results['summary']['passed']}")
        print(f"❌ Failed: {self.results['summary']['failed']}")
        print(f"⏭️ Skipped: {self.results['summary']['skipped']}")
        print("="*50)

    def run_all(self):
        """Run all tests and generate report."""
        print(f"🚀 Starting test run at {self.results['start_time']}")
        
        for test_file in self.test_files:
            test_path = self.root_dir / test_file
            if test_path.exists():
                self.results["tests"][test_file] = self.run_test(str(test_path))
            else:
                print(f"⚠️ Test file not found: {test_file}")
                self.results["summary"]["skipped"] += 1
        
        self.print_summary()
        self.save_results()
        
        # Return non-zero exit code if any tests failed
        return 1 if self.results["summary"]["failed"] > 0 else 0

def main():
    parser = argparse.ArgumentParser(description="Run Dream.OS tests")
    parser.add_argument("--category", choices=["core", "messaging", "ui", "tools"],
                      help="Run tests from a specific category")
    args = parser.parse_args()
    
    runner = TestRunner(category=args.category)
    sys.exit(runner.run_all())

if __name__ == "__main__":
    main() 