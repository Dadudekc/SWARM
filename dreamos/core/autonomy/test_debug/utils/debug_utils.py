"""
Test Debug Utilities
------------------
Shared utilities for test debugging functionality.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from dreamos.core.utils.file_utils import (
    atomic_write,
    safe_read,
    safe_write
)
from dreamos.core.utils.json_utils import (
    load_json,
    save_json,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestDebugUtils:
    """Shared utilities for test debugging."""
    
    @staticmethod
    def parse_test_failures(test_output: str) -> Dict[str, str]:
        """Parse test failures from test output.
        
        Args:
            test_output: Raw test output string
            
        Returns:
            Dictionary mapping test names to error messages
        """
        failures = {}
        current_test = None
        error_lines = []
        
        for line in test_output.splitlines():
            if line.startswith("FAILED "):
                # Extract test name
                test_name = line.split("FAILED ")[1].strip()
                current_test = test_name
                error_lines = []
            elif current_test and line.strip():
                error_lines.append(line)
                if line.startswith("AssertionError") or line.startswith("Error"):
                    failures[current_test] = "\n".join(error_lines)
                    current_test = None
                    error_lines = []
        
        return failures
    
    @staticmethod
    def create_fix_request(
        test_name: str,
        error: str,
        agent_id: str,
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a fix request for a test failure.
        
        Args:
            test_name: Name of failed test
            error: Error message
            agent_id: Agent identifier
            file_path: Optional path to test file
            
        Returns:
            Fix request dictionary
        """
        return {
            "id": f"{test_name}_{int(datetime.utcnow().timestamp())}",
            "test_name": test_name,
            "error": error,
            "agent_id": agent_id,
            "file_path": file_path,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending"
        }
    
    @staticmethod
    def save_fix_request(
        request: Dict[str, Any],
        outbox_dir: Path,
        logger: Optional[logging.Logger] = None
    ) -> bool:
        """Save a fix request to the outbox.
        
        Args:
            request: Fix request dictionary
            outbox_dir: Directory to save request
            logger: Optional logger instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create request file
            request_file = outbox_dir / f"fix_request_{request['id']}.json"
            
            # Save using shared utility
            return safe_write(request_file, request, logger)
            
        except Exception as e:
            if logger:
                logger.error(
                    platform="test_debug",
                    status="error",
                    message=f"Error saving fix request: {str(e)}",
                    tags=["request", "error"]
                )
            return False
    
    @staticmethod
    def load_fix_request(
        request_file: Path,
        logger: Optional[logging.Logger] = None
    ) -> Optional[Dict[str, Any]]:
        """Load a fix request from file.
        
        Args:
            request_file: Path to request file
            logger: Optional logger instance
            
        Returns:
            Fix request dictionary if successful, None otherwise
        """
        try:
            # Load using shared utility
            return load_json(request_file)
            
        except Exception as e:
            if logger:
                logger.error(
                    platform="test_debug",
                    status="error",
                    message=f"Error loading fix request: {str(e)}",
                    tags=["request", "error"]
                )
            return None
    
    @staticmethod
    def archive_fix_request(
        request_file: Path,
        archive_dir: Path,
        logger: Optional[logging.Logger] = None
    ) -> bool:
        """Archive a processed fix request.
        
        Args:
            request_file: Path to request file
            archive_dir: Directory to archive to
            logger: Optional logger instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Archive using shared utility
            return safe_write(request_file, None, logger)
            
        except Exception as e:
            if logger:
                logger.error(
                    platform="test_debug",
                    status="error",
                    message=f"Error archiving fix request: {str(e)}",
                    tags=["archive", "error"]
                )
            return False

class DebugUtils:
    """Utilities for test debugging operations."""
    
    @staticmethod
    def extract_agent_id(file_path: Path) -> Optional[str]:
        """Extract agent ID from a response file.
        
        Args:
            file_path: Path to the response file
            
        Returns:
            Agent ID if found, None otherwise
        """
        try:
            with open(file_path, 'r') as f:
                response = json.load(f)
            return response.get("agent_id")
        except Exception as e:
            logger.error(f"Error extracting agent ID from {file_path}: {e}")
            return None 
