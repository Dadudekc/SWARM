"""
Agent Resumer System

Manages agent resumption and handles test debug loop mode.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class AgentResumer:
    def __init__(self, base_dir: str = "config/agent_comms"):
        """Initialize the agent resumer system.
        
        Args:
            base_dir: Base directory for agent communications
        """
        self.base_dir = Path(base_dir)
        self.agent_status_file = self.base_dir / "agent_status.json"
        self.working_tasks_file = self.base_dir / "working_tasks.json"
        self.future_tasks_file = self.base_dir / "future_tasks.json"
        self.test_debug_log = self.base_dir / "debug_logs/test_debug.log"
        
        # Ensure directories exist
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.test_debug_log.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize files if they don't exist
        self._init_files()
        
    def _init_files(self):
        """Initialize required files with default content."""
        if not self.agent_status_file.exists():
            self._write_json(self.agent_status_file, {
                "cycle_count": 0,
                "last_active": None,
                "mode": "normal",
                "test_debug": {
                    "active": False,
                    "start_time": None,
                    "completed_cycles": 0
                }
            })
            
        if not self.working_tasks_file.exists():
            self._write_json(self.working_tasks_file, {
                "TEST_FIX": [],
                "BLOCKER-TEST-DEBUG": []
            })
            
        if not self.future_tasks_file.exists():
            self._write_json(self.future_tasks_file, {
                "pending_tasks": [],
                "completed_tasks": []
            })
            
    def _write_json(self, file_path: Path, data: Dict):
        """Write JSON data to file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
            
    def _read_json(self, file_path: Path) -> Dict:
        """Read JSON data from file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def activate_test_debug_mode(self):
        """Activate test debug loop mode."""
        status = self._read_json(self.agent_status_file)
        status["mode"] = "test_debug"
        status["test_debug"] = {
            "active": True,
            "start_time": datetime.now().isoformat(),
            "completed_cycles": 0
        }
        self._write_json(self.agent_status_file, status)
        
        # Log activation
        with open(self.test_debug_log, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now().isoformat()}] Test Debug Mode Activated\n")
            
    def increment_cycle(self):
        """Increment the cycle count."""
        status = self._read_json(self.agent_status_file)
        status["cycle_count"] += 1
        if status["mode"] == "test_debug":
            status["test_debug"]["completed_cycles"] += 1
        status["last_active"] = datetime.now().isoformat()
        self._write_json(self.agent_status_file, status)
        
    def reset_cycle_count(self):
        """Reset the cycle count."""
        status = self._read_json(self.agent_status_file)
        status["cycle_count"] = 0
        if status["mode"] == "test_debug":
            status["test_debug"]["completed_cycles"] = 0
        self._write_json(self.agent_status_file, status)
        
    def add_test_fix_task(self, task_data: Dict):
        """Add a new TEST_FIX task."""
        tasks = self._read_json(self.working_tasks_file)
        tasks["TEST_FIX"].append({
            **task_data,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        })
        self._write_json(self.working_tasks_file, tasks)
        
    def add_blocker_task(self, task_data: Dict):
        """Add a new BLOCKER-TEST-DEBUG task."""
        tasks = self._read_json(self.working_tasks_file)
        tasks["BLOCKER-TEST-DEBUG"].append({
            **task_data,
            "created_at": datetime.now().isoformat(),
            "status": "pending"
        })
        self._write_json(self.working_tasks_file, tasks)
        
    def log_test_debug(self, message: str):
        """Log a test debug message."""
        with open(self.test_debug_log, 'a', encoding='utf-8') as f:
            f.write(f"\n[{datetime.now().isoformat()}] {message}")
            
    def get_test_debug_status(self) -> Dict:
        """Get current test debug status."""
        status = self._read_json(self.agent_status_file)
        return {
            "mode": status["mode"],
            "cycle_count": status["cycle_count"],
            "test_debug": status["test_debug"]
        } 
