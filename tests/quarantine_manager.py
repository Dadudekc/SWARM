#!/usr/bin/env python3
"""
Test Quarantine Manager
Manages test quarantining based on attempt thresholds and platform-specific issues.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

class TestQuarantineManager:
    def __init__(self, analysis_file: str = "test_error_analysis.json"):
        self.analysis_file = Path(analysis_file)
        self.data = self._load_analysis()
        self.max_attempts = 4

    def _load_analysis(self) -> Dict:
        """Load test analysis data."""
        if not self.analysis_file.exists():
            return {
                "test_status": {
                    "total_tests": 0,
                    "passed_tests": 0,
                    "failed_tests": 0,
                    "quarantined_tests": 0
                },
                "quarantined_tests": [],
                "quarantine_metadata": {
                    "total_quarantined": 0,
                    "platform_impact": {"Windows": 0, "Linux": 0, "Mac": 0},
                    "last_review": None,
                    "review_frequency": "weekly",
                    "next_review": None,
                    "quarantine_criteria": {
                        "max_attempts": self.max_attempts,
                        "platform_specific": True,
                        "requires_architectural_changes": True
                    }
                }
            }
        
        with open(self.analysis_file, 'r') as f:
            return json.load(f)

    def _save_analysis(self) -> None:
        """Save test analysis data."""
        with open(self.analysis_file, 'w') as f:
            json.dump(self.data, f, indent=4)

    def should_quarantine(self, test_name: str, attempts: int, platform: str = "Windows") -> bool:
        """Determine if a test should be quarantined based on attempts and platform."""
        if attempts >= self.max_attempts:
            return True
        return False

    def quarantine_test(self, test_name: str, file: str, issue: str, 
                       platform_impact: str, root_cause: str, 
                       suggested_fix: str, impact_assessment: str,
                       attempts: int) -> None:
        """Quarantine a test with detailed information."""
        quarantine_entry = {
            "test_name": test_name,
            "file": file,
            "issue": issue,
            "platform_impact": platform_impact,
            "root_cause": root_cause,
            "suggested_fix": suggested_fix,
            "impact_assessment": impact_assessment,
            "quarantine_date": datetime.now().isoformat(),
            "last_reviewed": datetime.now().isoformat(),
            "attempts": attempts,
            "quarantine_reason": f"Exceeded {self.max_attempts}-attempt threshold for {issue}"
        }

        # Update test status
        if test_name in self.data["test_details"]:
            self.data["test_details"][test_name]["status"] = "quarantined"

        # Add to quarantined tests
        self.data["quarantined_tests"].append(quarantine_entry)

        # Update quarantine metadata
        self.data["quarantine_metadata"]["total_quarantined"] += 1
        self.data["quarantine_metadata"]["platform_impact"][platform_impact] += 1

        # Update test status counts
        self.data["test_status"]["quarantined_tests"] += 1
        self.data["test_status"]["failed_tests"] -= 1

        self._save_analysis()

    def remove_quarantine(self, test_name: str) -> None:
        """Remove a test from quarantine."""
        for i, test in enumerate(self.data["quarantined_tests"]):
            if test["test_name"] == test_name:
                # Update test status
                if test_name in self.data["test_details"]:
                    self.data["test_details"][test_name]["status"] = "active"

                # Remove from quarantined tests
                self.data["quarantined_tests"].pop(i)

                # Update quarantine metadata
                self.data["quarantine_metadata"]["total_quarantined"] -= 1
                self.data["quarantine_metadata"]["platform_impact"][test["platform_impact"]] -= 1

                # Update test status counts
                self.data["test_status"]["quarantined_tests"] -= 1
                self.data["test_status"]["failed_tests"] += 1

                self._save_analysis()
                break

    def get_quarantined_tests(self) -> List[Dict]:
        """Get list of quarantined tests."""
        return self.data["quarantined_tests"]

    def get_quarantine_stats(self) -> Dict:
        """Get quarantine statistics."""
        return {
            "total_quarantined": self.data["quarantine_metadata"]["total_quarantined"],
            "platform_impact": self.data["quarantine_metadata"]["platform_impact"],
            "last_review": self.data["quarantine_metadata"]["last_review"],
            "next_review": self.data["quarantine_metadata"]["next_review"]
        }

    def generate_task_list(self) -> Dict:
        """Generate a comprehensive task list categorizing fixes by difficulty."""
        tasks = {
            "easy_fixes": [],
            "medium_fixes": [],
            "hard_fixes": [],
            "quarantined": [],
            "summary": {
                "total_tests": self.data["test_status"]["total_tests"],
                "passed_tests": self.data["test_status"]["passed_tests"],
                "failed_tests": self.data["test_status"]["failed_tests"],
                "quarantined_tests": self.data["test_status"]["quarantined_tests"],
                "easy_fixes_count": 0,
                "medium_fixes_count": 0,
                "hard_fixes_count": 0
            }
        }

        # Process failed tests
        for test_name, details in self.data["test_details"].items():
            if details["status"] == "failed":
                task = {
                    "test_name": test_name,
                    "file": details.get("file", "unknown"),
                    "issue": details.get("issue", "unknown"),
                    "difficulty": details.get("difficulty", "medium"),
                    "error": details.get("error", "unknown"),
                    "suggested_fix": details.get("fix", "Needs investigation")
                }
                
                if details.get("difficulty") == "easy":
                    tasks["easy_fixes"].append(task)
                    tasks["summary"]["easy_fixes_count"] += 1
                elif details.get("difficulty") == "hard":
                    tasks["hard_fixes"].append(task)
                    tasks["summary"]["hard_fixes_count"] += 1
                else:
                    tasks["medium_fixes"].append(task)
                    tasks["summary"]["medium_fixes_count"] += 1

        # Process quarantined tests
        for test in self.data["quarantined_tests"]:
            tasks["quarantined"].append({
                "test_name": test["test_name"],
                "file": test["file"],
                "issue": test["issue"],
                "platform_impact": test["platform_impact"],
                "root_cause": test["root_cause"],
                "suggested_fix": test["suggested_fix"],
                "attempts": test["attempts"],
                "quarantine_date": test["quarantine_date"]
            })

        return tasks

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a comprehensive report of test fixes and quarantined tests."""
        tasks = self.generate_task_list()
        
        report = []
        report.append("# Test Fix Report")
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        
        # Summary
        report.append("## Summary")
        report.append(f"- Total Tests: {tasks['summary']['total_tests']}")
        report.append(f"- Passed Tests: {tasks['summary']['passed_tests']}")
        report.append(f"- Failed Tests: {tasks['summary']['failed_tests']}")
        report.append(f"- Quarantined Tests: {tasks['summary']['quarantined_tests']}")
        report.append(f"- Easy Fixes: {tasks['summary']['easy_fixes_count']}")
        report.append(f"- Medium Fixes: {tasks['summary']['medium_fixes_count']}")
        report.append(f"- Hard Fixes: {tasks['summary']['hard_fixes_count']}\n")

        # Easy Fixes
        if tasks["easy_fixes"]:
            report.append("## Easy Fixes")
            for task in tasks["easy_fixes"]:
                report.append(f"### {task['test_name']}")
                report.append(f"- File: {task['file']}")
                report.append(f"- Issue: {task['issue']}")
                report.append(f"- Error: {task['error']}")
                report.append(f"- Fix: {task['suggested_fix']}\n")

        # Medium Fixes
        if tasks["medium_fixes"]:
            report.append("## Medium Fixes")
            for task in tasks["medium_fixes"]:
                report.append(f"### {task['test_name']}")
                report.append(f"- File: {task['file']}")
                report.append(f"- Issue: {task['issue']}")
                report.append(f"- Error: {task['error']}")
                report.append(f"- Fix: {task['suggested_fix']}\n")

        # Hard Fixes
        if tasks["hard_fixes"]:
            report.append("## Hard Fixes")
            for task in tasks["hard_fixes"]:
                report.append(f"### {task['test_name']}")
                report.append(f"- File: {task['file']}")
                report.append(f"- Issue: {task['issue']}")
                report.append(f"- Error: {task['error']}")
                report.append(f"- Fix: {task['suggested_fix']}\n")

        # Quarantined Tests
        if tasks["quarantined"]:
            report.append("## Quarantined Tests")
            for task in tasks["quarantined"]:
                report.append(f"### {task['test_name']}")
                report.append(f"- File: {task['file']}")
                report.append(f"- Issue: {task['issue']}")
                report.append(f"- Platform Impact: {task['platform_impact']}")
                report.append(f"- Root Cause: {task['root_cause']}")
                report.append(f"- Suggested Fix: {task['suggested_fix']}")
                report.append(f"- Attempts: {task['attempts']}")
                report.append(f"- Quarantine Date: {task['quarantine_date']}\n")

        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
        
        return report_text

def main():
    """Main function for command-line usage."""
    import argparse
    parser = argparse.ArgumentParser(description="Manage test quarantining")
    parser.add_argument("--quarantine", action="store_true", help="Quarantine a test")
    parser.add_argument("--remove", action="store_true", help="Remove test from quarantine")
    parser.add_argument("--test", help="Test name")
    parser.add_argument("--file", help="Test file path")
    parser.add_argument("--issue", help="Issue description")
    parser.add_argument("--platform", default="Windows", help="Platform impact")
    parser.add_argument("--root-cause", help="Root cause of the issue")
    parser.add_argument("--fix", help="Suggested fix")
    parser.add_argument("--impact", help="Impact assessment")
    parser.add_argument("--attempts", type=int, help="Number of fix attempts")
    parser.add_argument("--list", action="store_true", help="List quarantined tests")
    parser.add_argument("--stats", action="store_true", help="Show quarantine statistics")
    parser.add_argument("--report", action="store_true", help="Generate fix report")
    parser.add_argument("--output", help="Output file for report")

    args = parser.parse_args()
    manager = TestQuarantineManager()

    if args.report:
        print(manager.generate_report(args.output))
    elif args.list:
        print(json.dumps(manager.get_quarantined_tests(), indent=2))
    elif args.stats:
        print(json.dumps(manager.get_quarantine_stats(), indent=2))
    elif args.quarantine:
        if not all([args.test, args.file, args.issue, args.root_cause, args.fix, args.impact, args.attempts]):
            print("Error: All fields required for quarantining")
            return
        manager.quarantine_test(
            args.test, args.file, args.issue, args.platform,
            args.root_cause, args.fix, args.impact, args.attempts
        )
    elif args.remove:
        if not args.test:
            print("Error: Test name required for removal")
            return
        manager.remove_quarantine(args.test)

if __name__ == "__main__":
    main() 