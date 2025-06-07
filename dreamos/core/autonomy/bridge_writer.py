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
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import aiofiles

from ..logging.log_manager import LogManager
from .error import ErrorTracker, ErrorHandler, ErrorSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeWriter:
    """Manages writing responses to the bridge."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge writer.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        # Initialize components
        self.logger = LogManager()
        
        # Initialize error handling
        self.error_tracker = ErrorTracker()
        self.error_handler = ErrorHandler(self.error_tracker)
        
        # Bridge configuration
        self.bridge_dir = Path(self.config.get("bridge_dir", "bridge_outbox"))
        self.bridge_dir.mkdir(exist_ok=True)
        self.max_retries = self.config.get("max_retries", 3)
        self.write_timeout = self.config.get("write_timeout", 30)  # 30 seconds
        
        # Initialize logging
        self.logger.info(
            platform="bridge_writer",
            status="initialized",
            message="Bridge writer initialized",
            tags=["init", "bridge"]
        )
    
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
            
            # Write with retry
            await self.error_handler.with_retry(
                operation="write_response",
                agent_id=agent_id,
                func=self._write_file,
                filepath=filepath,
                data=response
            )
            
            self.logger.info(
                platform="bridge_writer",
                status="success",
                message=f"Wrote response for agent {agent_id}",
                tags=["write", "success"]
            )
            return True
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.HIGH,
                agent_id=agent_id,
                context={
                    "operation": "write_response",
                    "response": response
                }
            )
            self.logger.error(
                platform="bridge_writer",
                status="error",
                message=f"Error writing response: {str(e)}",
                tags=["write", "error"]
            )
            return False
    
    async def _write_file(self, filepath: Path, data: Dict[str, Any]):
        """Write data to a file atomically.
        
        Args:
            filepath: Path to write to
            data: Data to write
        """
        # Create temp file
        temp_path = filepath.with_suffix(".tmp")
        
        try:
            # Write to temp file
            async with aiofiles.open(temp_path, "w") as f:
                await f.write(json.dumps(data, indent=2))
            
            # Atomic rename
            temp_path.rename(filepath)
            
        except Exception as e:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise
    
    async def cleanup_old_responses(self, max_age_hours: int = 24):
        """Clean up old response files.
        
        Args:
            max_age_hours: Maximum age of files in hours
        """
        try:
            # Get current time
            now = datetime.now()
            
            # Find old files
            for filepath in self.bridge_dir.glob("*.json"):
                # Get file age
                age = now - datetime.fromtimestamp(filepath.stat().st_mtime)
                age_hours = age.total_seconds() / 3600
                
                # Delete if too old
                if age_hours > max_age_hours:
                    await self.error_handler.with_retry(
                        operation="cleanup_file",
                        agent_id="bridge_writer",
                        func=self._delete_file,
                        filepath=filepath
                    )
            
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.MEDIUM,
                agent_id="bridge_writer",
                context={"operation": "cleanup_old_responses"}
            )
            self.logger.error(
                platform="bridge_writer",
                status="error",
                message=f"Error cleaning up old responses: {str(e)}",
                tags=["cleanup", "error"]
            )
    
    async def _delete_file(self, filepath: Path):
        """Delete a file.
        
        Args:
            filepath: Path to delete
        """
        try:
            filepath.unlink()
        except Exception as e:
            self.error_tracker.record_error(
                error_type=type(e).__name__,
                message=str(e),
                severity=ErrorSeverity.LOW,
                agent_id="bridge_writer",
                context={"operation": "delete_file", "filepath": str(filepath)}
            )
            raise 