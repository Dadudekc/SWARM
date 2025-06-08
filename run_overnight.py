"""
Run Overnight Tests
-----------------
Simple wrapper to run the overnight test runner.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the test runner
from agent_tools.swarm_tools.tests.overnight_test_runner import run

if __name__ == "__main__":
    run() 
