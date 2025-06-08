"""
Run Overnight Tests
-----------------
Script to run the overnight test runner.
"""

from agent_tools.swarm_tools.tests.overnight_test_runner import TestRunner

def main():
    """Main entry point."""
    runner = TestRunner()
    runner.run()

if __name__ == "__main__":
    main() 
