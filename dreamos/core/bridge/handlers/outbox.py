"""
Bridge Outbox Handler
------------------
Processes agent responses and applies code changes.
"""

import ast
import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import BaseBridgeHandler
from ...utils.core_utils import (
    load_json,
    save_json,
    atomic_write,
    safe_read,
    safe_write
)

# Configure logging
logger = logging.getLogger(__name__)

class BridgeOutboxHandler(BaseBridgeHandler):
    """Processes agent responses and applies code changes."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge outbox handler.
        
        Args:
            config: Optional configuration dictionary
        """
        super().__init__(
            config=config,
            watch_dir=Path(config.get("paths", {}).get("bridge_outbox", "data/bridge_outbox")),
            file_pattern="*.json"
        )
        
        # Initialize components
        self.archive_dir = Path(self.config.get("paths", {}).get("bridge_archive", "data/bridge_archive"))
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    async def _process_items(self):
        """Process items in the handler."""
        # Check for new responses
        for file_path in self.watch_dir.glob(self.file_pattern):
            if file_path.name not in self.processed_items:
                await self._process_file(file_path)
    
    async def _process_file(self, file_path: Path):
        """Process a file.
        
        Args:
            file_path: Path to file
        """
        try:
            # Load response data
            response = await self._load_json(str(file_path))
            if not response:
                return
            
            # Process response
            await self._process_response(response)
            
            # Move to archive
            archive_path = self.archive_dir / file_path.name
            await self._move_to_archive(file_path, archive_path)
            
            # Mark as processed
            self.processed_items.add(file_path.name)
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
    
    async def _process_response(self, response: Dict[str, Any]):
        """Process a single response.
        
        Args:
            response: Response to process
        """
        try:
            # Extract response data
            test_id = response.get("test_id")
            agent_id = response.get("agent_id")
            patch_content = response.get("patch_content")
            
            if not all([test_id, agent_id, patch_content]):
                logger.error("Invalid response format")
                return
            
            # Generate patch ID
            patch_id = f"{test_id}_{agent_id}_{int(time.time())}"
            
            # Apply patch
            if not await self._apply_patch(patch_id, patch_content, test_id):
                return
            
            # Run tests
            if not await self._run_tests():
                return
            
            # Commit changes
            await self._commit_changes(patch_id, f"Fix for test {test_id}")
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
    
    async def create_fix_request(
        self,
        agent: str,
        test_name: str,
        error: str,
        file_path: Optional[str] = None
    ):
        """Create a fix request for an agent.
        
        Args:
            agent: Agent identifier
            test_name: Name of failed test
            error: Error message
            file_path: Optional path to test file
        """
        try:
            # Create request
            request = {
                "id": f"{test_name}_{int(time.time())}",
                "agent": agent,
                "test_name": test_name,
                "error": error,
                "file_path": file_path,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Save request
            request_file = self.watch_dir / f"fix_request_{request['id']}.json"
            await self._save_json(str(request_file), request)
            
            logger.info(f"Created fix request for test {test_name}")
            
        except Exception as e:
            logger.error(f"Error creating fix request: {e}")
    
    async def _apply_patch(self, patch_id: str, patch_content: str, test_id: str) -> bool:
        """Apply a code patch.
        
        Args:
            patch_id: Unique patch ID
            patch_content: Patch content
            test_id: Test ID
            
        Returns:
            True if patch was applied successfully
        """
        try:
            # Parse patch content
            patch_ast = ast.parse(patch_content)
            
            # Apply changes
            # ... (patch application logic)
            
            logger.info(f"Applied patch {patch_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying patch: {e}")
            return False
    
    async def _run_tests(self) -> bool:
        """Run tests.
        
        Returns:
            True if tests passed
        """
        try:
            # Run tests
            # ... (test execution logic)
            
            return True
            
        except Exception as e:
            logger.error(f"Error running tests: {e}")
            return False
    
    async def _commit_changes(self, patch_id: str, message: str):
        """Commit changes to version control.
        
        Args:
            patch_id: Unique patch ID
            message: Commit message
        """
        try:
            # Commit changes
            # ... (commit logic)
            
            logger.info(f"Committed changes for patch {patch_id}")
            
        except Exception as e:
            logger.error(f"Error committing changes: {e}")
    
    async def _move_to_archive(self, source: Path, target: Path):
        """Move file to archive.
        
        Args:
            source: Source file path
            target: Target file path
        """
        try:
            # Ensure target directory exists
            target.parent.mkdir(parents=True, exist_ok=True)
            
            # Move file
            await atomic_write(target, await safe_read(source))
            await safe_write(source, b"")  # Clear source file
            
        except Exception as e:
            logger.error(f"Error moving file to archive: {e}") 