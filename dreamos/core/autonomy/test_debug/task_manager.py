"""
Task Manager
-----------
Handles task creation, updates, and management.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from .utils.config import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskManager:
    """Manages task creation and updates."""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the task manager.
        
        Args:
            config_manager: Optional configuration manager
        """
        self.config_manager = config_manager or ConfigManager("config/test_debug_config.json")
        
        # Set up paths
        self.working_tasks_path = Path("working_tasks.json")
        self.future_tasks_path = Path("future_tasks.json")
        
        # Initialize task sets
        self.working_tasks: Set[str] = set()
        self.future_tasks: Set[str] = set()
        
        # Load initial state
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from files."""
        try:
            # Load working tasks
            if self.working_tasks_path.exists():
                with open(self.working_tasks_path, 'r') as f:
                    tasks = json.load(f)
                    self.working_tasks = set(tasks.keys())
            
            # Load future tasks
            if self.future_tasks_path.exists():
                with open(self.future_tasks_path, 'r') as f:
                    tasks = json.load(f)
                    self.future_tasks = set(tasks.keys())
                    
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to files."""
        try:
            # Save working tasks
            with open(self.working_tasks_path, 'w') as f:
                json.dump(self._get_working_tasks(), f, indent=2)
            
            # Save future tasks
            with open(self.future_tasks_path, 'w') as f:
                json.dump(self._get_future_tasks(), f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving tasks: {e}")
    
    def _get_working_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all working tasks.
        
        Returns:
            Dictionary of working tasks
        """
        try:
            if self.working_tasks_path.exists():
                with open(self.working_tasks_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    def _get_future_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all future tasks.
        
        Returns:
            Dictionary of future tasks
        """
        try:
            if self.future_tasks_path.exists():
                with open(self.future_tasks_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception:
            return {}
    
    async def create_fix_task(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task to fix a test failure.
        
        Args:
            failure: Test failure details
            
        Returns:
            Created task
        """
        try:
            # Create task
            task = {
                "id": str(uuid.uuid4()),
                "type": "TEST_FIX",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data": {
                    "test_name": failure["name"],
                    "test_file": self._get_test_file(failure["name"]),
                    "error": failure["error"],
                    "attempts": 0
                }
            }
            
            # Add to working tasks
            tasks = self._get_working_tasks()
            tasks[task["id"]] = task
            self.working_tasks.add(task["id"])
            
            # Save tasks
            self._save_tasks()
            
            return task
            
        except Exception as e:
            logger.error(f"Error creating fix task: {e}")
            return None
    
    async def create_blocker_task(self, task: Dict[str, Any]):
        """Create a blocker task for a failed fix.
        
        Args:
            task: Original task that failed
        """
        try:
            # Create blocker task
            blocker = {
                "id": str(uuid.uuid4()),
                "type": "BLOCKER",
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "data": {
                    "blocked_task_id": task["id"],
                    "test_name": task["data"]["test_name"],
                    "test_file": task["data"]["test_file"],
                    "error": task["data"]["error"],
                    "reason": "Fix attempt failed"
                }
            }
            
            # Add to future tasks
            tasks = self._get_future_tasks()
            tasks[blocker["id"]] = blocker
            self.future_tasks.add(blocker["id"])
            
            # Save tasks
            self._save_tasks()
            
        except Exception as e:
            logger.error(f"Error creating blocker task: {e}")
    
    async def update_task_status(self, task: Dict[str, Any], status: str):
        """Update task status.
        
        Args:
            task: Task to update
            status: New status
        """
        try:
            # Update task
            task["status"] = status
            task["updated_at"] = datetime.utcnow().isoformat()
            
            # Update in working tasks
            tasks = self._get_working_tasks()
            if task["id"] in tasks:
                tasks[task["id"]] = task
                
                # Remove if completed
                if status in ["completed", "failed"]:
                    self.working_tasks.discard(task["id"])
            
            # Save tasks
            self._save_tasks()
            
        except Exception as e:
            logger.error(f"Error updating task status: {e}")
    
    def has_pending_changes(self) -> bool:
        """Check if there are pending changes.
        
        Returns:
            True if there are pending changes, False otherwise
        """
        try:
            # Check working tasks
            tasks = self._get_working_tasks()
            for task in tasks.values():
                if task["status"] == "pending":
                    return True
            
            # Check future tasks
            tasks = self._get_future_tasks()
            for task in tasks.values():
                if task["status"] == "pending":
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking pending changes: {e}")
            return False
    
    def _get_test_file(self, test_name: str) -> Optional[str]:
        """Get test file path from test name.
        
        Args:
            test_name: Test name
            
        Returns:
            Test file path if found, None otherwise
        """
        try:
            # Look for test file
            for path in Path("tests").rglob("test_*.py"):
                with open(path, 'r') as f:
                    content = f.read()
                    if test_name in content:
                        return str(path)
            return None
            
        except Exception as e:
            logger.error(f"Error finding test file: {e}")
            return None 
