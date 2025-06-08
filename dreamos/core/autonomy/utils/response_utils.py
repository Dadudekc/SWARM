"""
Response Utilities
----------------
Shared utilities for response processing.
"""

import json
import logging
import asyncio
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResourceManager:
    """Manages resource allocation and limits."""
    
    def __init__(self, max_concurrent: int = 10):
        """Initialize resource manager.
        
        Args:
            max_concurrent: Maximum concurrent operations
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks = set()
    
    async def __aenter__(self):
        """Acquire resource."""
        await self.semaphore.acquire()
        task = asyncio.current_task()
        self._active_tasks.add(task)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Release resource."""
        task = asyncio.current_task()
        self._active_tasks.remove(task)
        self.semaphore.release()

class ResponseErrorHandler:
    """Handles response processing errors."""
    
    def __init__(self, max_retries: int = 3):
        """Initialize error handler.
        
        Args:
            max_retries: Maximum retry attempts
        """
        self.max_retries = max_retries
        self._retry_counts = {}
    
    async def handle_error(self, error: Exception, response_id: str) -> bool:
        """Handle processing error.
        
        Args:
            error: Exception that occurred
            response_id: ID of response being processed
            
        Returns:
            True if should retry, False otherwise
        """
        if response_id not in self._retry_counts:
            self._retry_counts[response_id] = 0
        
        if self._retry_counts[response_id] < self.max_retries:
            self._retry_counts[response_id] += 1
            await asyncio.sleep(2 ** self._retry_counts[response_id])
            return True
        return False

def load_response_file(response_file: Path) -> Tuple[Dict[str, Any], Optional[str]]:
    """Load response data from file.
    
    Args:
        response_file: Path to response file
        
    Returns:
        Tuple of (response_data, error_message)
    """
    try:
        with open(response_file, 'r') as f:
            return json.load(f), None
    except Exception as e:
        return {}, f"Error loading response file: {e}"

def archive_response_file(response_file: Path, archive_dir: Path) -> Tuple[bool, Optional[str]]:
    """Archive a processed response file.
    
    Args:
        response_file: Path to response file
        archive_dir: Path to archive directory
        
    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Create archive directory if needed
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        # Move to archive
        archive_path = archive_dir / response_file.name
        shutil.move(str(response_file), str(archive_path))
        
        return True, None
        
    except Exception as e:
        return False, f"Error archiving response file: {e}"

def extract_agent_id_from_file(response_file: Path) -> Tuple[Optional[str], Optional[str]]:
    """Extract agent ID from response file.
    
    Args:
        response_file: Path to response file
        
    Returns:
        Tuple of (agent_id, error_message)
    """
    try:
        with open(response_file, 'r') as f:
            response = json.load(f)
            agent_id = response.get("agent_id")
            if not agent_id:
                return None, "No agent_id found in response"
            return agent_id, None
    except Exception as e:
        return None, f"Error extracting agent ID: {e}"

def validate_response(response: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate response data.
    
    Args:
        response: Response data
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["agent_id", "timestamp", "type"]
    
    for field in required_fields:
        if field not in response:
            return False, f"Missing required field: {field}"
    
    return True, None 
