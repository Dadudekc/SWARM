"""
Bridge Writer
------------
Manages writing responses to the bridge by:
1. Writing response files
2. Managing file operations
3. Handling write errors
4. Tracking write status
5. Ensuring atomic writes

Optimized for reliable file operations.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..utils.file_utils import (
    async_atomic_write,
    async_delete_file,
    cleanup_old_files,
    async_save_json
)
from ..utils.core_utils import (
    ErrorTracker,
    async_retry,
    track_operation
)
from ..utils.logging_utils import (
    PlatformEventLogger,
    StatusTracker
)

# Configure logging
logger = logging.getLogger(__name__)

class BridgeWriter:
    """Manages writing responses to the bridge."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge writer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Bridge configuration
        self.bridge_dir = Path(self.config.get("bridge_dir", "bridge_outbox"))
        self.bridge_dir.mkdir(exist_ok=True)
        self.max_retries = self.config.get("max_retries", 3)
        self.write_timeout = self.config.get("write_timeout", 30)  # 30 seconds
        
        # Initialize components
        self.error_tracker = ErrorTracker()
        self.event_logger = PlatformEventLogger(
            log_dir=self.bridge_dir / "logs",
            platform="bridge_writer"
        )
        self.status_tracker = StatusTracker("bridge_writer")
        
        # Initialize logging
        self.event_logger.log_event(
            event_type="init",
            status="success",
            message="Bridge writer initialized",
            tags=["init", "bridge"]
        )
    
    @async_retry(max_retries=3, delay=1.0, backoff=2.0)
    @track_operation("write_response")
    async def write_response(self, agent_id: str, response: Dict[str, Any]) -> bool:
        """Write a response to the bridge.
        
        Args:
            agent_id: ID of the agent
            response: Response data to write
            
        Returns:
            True if write successful, False otherwise
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{agent_id}_{timestamp}.json"
            filepath = self.bridge_dir / filename
            
            # Write response
            success = await async_save_json(filepath, response, logger)
            
            if success:
                self.event_logger.log_event(
                    event_type="write_response",
                    status="success",
                    message=f"Wrote response for agent {agent_id}",
                    tags=["write", "success"],
                    data={"agent_id": agent_id, "filepath": str(filepath)}
                )
                self.status_tracker.update_status("write_response", True)
                return True
            else:
                raise Exception("Failed to write response file")
            
        except Exception as e:
            self.error_tracker.add_error(
                error=e,
                operation="write_response",
                context={
                    "agent_id": agent_id,
                    "response": response
                }
            )
            self.event_logger.log_event(
                event_type="write_response",
                status="error",
                message=f"Error writing response: {str(e)}",
                tags=["write", "error"],
                data={"agent_id": agent_id, "error": str(e)}
            )
            self.status_tracker.update_status("write_response", False, e)
            return False
    
    @async_retry(max_retries=3, delay=1.0, backoff=2.0)
    @track_operation("cleanup_old_responses")
    async def cleanup_old_responses(self, max_age_hours: int = 24):
        """Clean up old response files.
        
        Args:
            max_age_hours: Maximum age of files in hours
        """
        try:
            deleted_files = await cleanup_old_files(
                directory=self.bridge_dir,
                max_age_hours=max_age_hours,
                pattern="*.json",
                logger=logger
            )
            
            self.event_logger.log_event(
                event_type="cleanup",
                status="success",
                message=f"Cleaned up {len(deleted_files)} old files",
                tags=["cleanup", "success"],
                data={"deleted_files": [str(f) for f in deleted_files]}
            )
            self.status_tracker.update_status("cleanup_old_responses", True)
            
        except Exception as e:
            self.error_tracker.add_error(
                error=e,
                operation="cleanup_old_responses"
            )
            self.event_logger.log_event(
                event_type="cleanup",
                status="error",
                message=f"Error cleaning up old responses: {str(e)}",
                tags=["cleanup", "error"]
            )
            self.status_tracker.update_status("cleanup_old_responses", False, e)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bridge writer status.
        
        Returns:
            Status dictionary
        """
        return {
            "status": self.status_tracker.get_status(),
            "errors": self.error_tracker.get_errors(),
            "events": self.event_logger.get_events(limit=10)
        } 