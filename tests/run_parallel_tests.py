#!/usr/bin/env python3
"""
Parallel test execution coordinator.
Manages test execution across multiple agents in parallel.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

TEST_ANALYSIS_FILE = Path(__file__).parent / "test_error_analysis.json"
AGENT_COORDS_FILE = Path(__file__).parent.parent / "runtime" / "config" / "cursor_agent_coords.json"

def load_test_analysis() -> Dict:
    """Load test analysis data."""
    if not TEST_ANALYSIS_FILE.exists():
        return {
            "claimed_tests": {},
            "test_status": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "in_progress": 0
            },
            "agent_assignments": {},
            "last_run": None,
            "test_history": []
        }
    
    with open(TEST_ANALYSIS_FILE, 'r') as f:
        return json.load(f)

def save_test_analysis(data: Dict) -> None:
    """Save test analysis data."""
    with open(TEST_ANALYSIS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def claim_test(test_name: str, agent_id: str, issue: str) -> bool:
    """Claim a test for an agent."""
    data = load_test_analysis()
    
    if test_name in data["claimed_tests"]:
        return False
    
    data["claimed_tests"][test_name] = {
        "agent": agent_id,
        "status": "in_progress",
        "issue": issue,
        "claimed_at": datetime.now().isoformat(),
        "fix_attempts": []
    }
    
    data["test_status"]["in_progress"] += 1
    save_test_analysis(data)
    return True

def release_test(test_name: str) -> None:
    """Release a test claim."""
    data = load_test_analysis()
    
    if test_name in data["claimed_tests"]:
        del data["claimed_tests"][test_name]
        data["test_status"]["in_progress"] -= 1
        save_test_analysis(data)

def update_test_status(test_name: str, status: str, fix_attempt: Optional[str] = None) -> None:
    """Update test status and record fix attempt."""
    data = load_test_analysis()
    
    if test_name in data["claimed_tests"]:
        data["claimed_tests"][test_name]["status"] = status
        if fix_attempt:
            data["claimed_tests"][test_name]["fix_attempts"].append({
                "attempt": fix_attempt,
                "timestamp": datetime.now().isoformat()
            })
        save_test_analysis(data)

def run_tests(test_path: Optional[str] = None, agent_id: Optional[str] = None) -> None:
    """Run tests with parallel execution."""
    cmd = [
        "pytest",
        "-v",
        "-n", "auto",
        "--lf",
        "--maxfail=1",
        "--tb=short"
    ]
    
    if test_path:
        cmd.append(test_path)
    
    if agent_id:
        cmd.extend(["--agent-id", agent_id])
    
    subprocess.run(cmd)

def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python run_parallel_tests.py [command] [args]")
        print("Commands:")
        print("  claim <test_name> <agent_id> <issue>")
        print("  release <test_name>")
        print("  update <test_name> <status> [fix_attempt]")
        print("  run [test_path] [agent_id]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "claim":
        if len(sys.argv) < 5:
            print("Usage: python run_parallel_tests.py claim <test_name> <agent_id> <issue>")
            sys.exit(1)
        test_name, agent_id, issue = sys.argv[2:5]
        if claim_test(test_name, agent_id, issue):
            print(f"Test {test_name} claimed by agent {agent_id}")
        else:
            print(f"Test {test_name} is already claimed")
    
    elif command == "release":
        if len(sys.argv) < 3:
            print("Usage: python run_parallel_tests.py release <test_name>")
            sys.exit(1)
        test_name = sys.argv[2]
        release_test(test_name)
        print(f"Test {test_name} released")
    
    elif command == "update":
        if len(sys.argv) < 4:
            print("Usage: python run_parallel_tests.py update <test_name> <status> [fix_attempt]")
            sys.exit(1)
        test_name = sys.argv[2]
        status = sys.argv[3]
        fix_attempt = sys.argv[4] if len(sys.argv) > 4 else None
        update_test_status(test_name, status, fix_attempt)
        print(f"Test {test_name} status updated to {status}")
    
    elif command == "run":
        test_path = sys.argv[2] if len(sys.argv) > 2 else None
        agent_id = sys.argv[3] if len(sys.argv) > 3 else None
        run_tests(test_path, agent_id)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main() 