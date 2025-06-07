"""
State Management
--------------
Manages state persistence and retrieval for the test debug system.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StateManager:
    """Manages state persistence and retrieval."""
    
    def __init__(self, state_path: str = "runtime/agent_status.json"):
        """Initialize the state manager.
        
        Args:
            state_path: Path to state file
        """
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize state
        self.cycle_count = 0
        self.failed_tests = set()
        self.passed_tests = set()
        self.processing_tests = set()
        
        # Load initial state
        self._load_state()
    
    def _load_state(self):
        """Load state from file."""
        try:
            if self.state_path.exists():
                with open(self.state_path, 'r') as f:
                    state = json.load(f)
                    self.cycle_count = state.get("cycle_count", 0)
                    self.failed_tests = set(state.get("failed_tests", []))
                    self.passed_tests = set(state.get("passed_tests", []))
                    self.processing_tests = set(state.get("processing_tests", []))
        except Exception as e:
            logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save state to file."""
        try:
            state = {
                "cycle_count": self.cycle_count,
                "failed_tests": list(self.failed_tests),
                "passed_tests": list(self.passed_tests),
                "processing_tests": list(self.processing_tests),
                "timestamp": datetime.utcnow().isoformat()
            }
            with open(self.state_path, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def increment_cycle(self):
        """Increment cycle count and save state."""
        self.cycle_count += 1
        self.save_state()
    
    def add_failed_test(self, test_name: str):
        """Add a failed test to tracking.
        
        Args:
            test_name: Name of the failed test
        """
        self.failed_tests.add(test_name)
        self.save_state()
    
    def add_passed_test(self, test_name: str):
        """Add a passed test to tracking.
        
        Args:
            test_name: Name of the passed test
        """
        self.passed_tests.add(test_name)
        self.save_state()
    
    def add_processing_test(self, test_name: str):
        """Add a test to processing tracking.
        
        Args:
            test_name: Name of the test being processed
        """
        self.processing_tests.add(test_name)
        self.save_state()
    
    def remove_processing_test(self, test_name: str):
        """Remove a test from processing tracking.
        
        Args:
            test_name: Name of the test to remove
        """
        self.processing_tests.discard(test_name)
        self.save_state()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current state.
        
        Returns:
            Current state dictionary
        """
        return {
            "cycle_count": self.cycle_count,
            "failed_tests": list(self.failed_tests),
            "passed_tests": list(self.passed_tests),
            "processing_tests": list(self.processing_tests),
            "timestamp": datetime.utcnow().isoformat()
        } 