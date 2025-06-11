"""
Base Tracker
-----------
Base class for tracking and logging operations.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Set
from datetime import datetime

logger = logging.getLogger(__name__)

class BaseTracker:
    """Base class for tracking and logging operations."""
    
    def __init__(
        self,
        log_dir: Optional[str] = None,
        platform: str = "base",
        tracker_type: str = "tracker"
    ):
        """Initialize the tracker.
        
        Args:
            log_dir: Directory to store logs
            platform: Platform identifier for logging
            tracker_type: Type of tracker for logging
        """
        self.log_dir = Path(log_dir or "runtime/logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.platform = platform
        self.tracker_type = tracker_type
        self.logger = logger
        
        # Initialize logging
        self.logger.info(
            f"{self.__class__.__name__} initialized",
            extra={
                "platform": self.platform,
                "status": "initialized",
                "tags": ["init", self.tracker_type]
            }
        )
    
    def _log_failure(
        self,
        item_id: str,
        data: Dict[str, Any],
        failure_type: str = "failure"
    ) -> None:
        """Log a failure event.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to log
            failure_type: Type of failure
        """
        try:
            # Add common metadata
            log_data = {
                "item_id": item_id,
                "timestamp": datetime.now().isoformat(),
                "failure_type": failure_type,
                **data
            }
            
            # Write to log file
            log_path = self.log_dir / f"{item_id}.json"
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
                
            self.logger.error(
                f"Logged {failure_type} for {item_id}",
                extra={
                    "platform": self.platform,
                    "status": failure_type,
                    "item_id": item_id,
                    "tags": ["log", failure_type]
                }
            )
        except Exception as e:
            self.logger.error(f"Error logging failure: {e}")
    
    def _log_success(
        self,
        item_id: str,
        data: Dict[str, Any],
        success_type: str = "success"
    ) -> None:
        """Log a success event.
        
        Args:
            item_id: Unique identifier for the item
            data: Data to log
            success_type: Type of success
        """
        try:
            # Add common metadata
            log_data = {
                "item_id": item_id,
                "timestamp": datetime.now().isoformat(),
                "success_type": success_type,
                **data
            }
            
            # Write to log file
            log_path = self.log_dir / f"{item_id}.json"
            with open(log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2)
                
            self.logger.info(
                f"Logged {success_type} for {item_id}",
                extra={
                    "platform": self.platform,
                    "status": success_type,
                    "item_id": item_id,
                    "tags": ["log", success_type]
                }
            )
        except Exception as e:
            self.logger.error(f"Error logging success: {e}")
    
    def _load_log(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Load a log file.
        
        Args:
            item_id: Unique identifier for the item
            
        Returns:
            Log data if found, None otherwise
        """
        try:
            log_path = self.log_dir / f"{item_id}.json"
            if log_path.exists():
                with open(log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading log for {item_id}: {e}")
        return None 