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

from ...logging.log_manager import LogManager
from .base_bridge_handler import BaseBridgeHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
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
    
    async def _process_items(self):
        """Process items in the handler."""
        # Check for new responses
        responses = await self.agent_loop._load_inbox("autonomy_agent")
        
        for response in responses:
            response_id = response.get("id")
            if response_id and response_id not in self.processed_items:
                await self._process_response(response)
                self.processed_items.add(response_id)
    
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
            
            # Mark as processed
            self.processed_items.add(response.get("id", file_path.name))
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error processing file {file_path}: {str(e)}",
                tags=["process", "error"]
            )
    
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
                self.logger.error(
                    platform="bridge_outbox",
                    status="error",
                    message="Invalid response format",
                    tags=["process", "error"]
                )
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
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error processing response: {str(e)}",
                tags=["process", "error"]
            )
    
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
            
            self.logger.info(
                platform="bridge_outbox",
                status="success",
                message=f"Applied patch {patch_id}",
                tags=["patch", "success"]
            )
            return True
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error applying patch: {str(e)}",
                tags=["patch", "error"]
            )
            return False
    
    async def create_fix_request(self, agent: str, test_name: str, error: str, file_path: Optional[str] = None):
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
            
            self.logger.info(
                platform="bridge_outbox",
                status="success",
                message=f"Created fix request for test {test_name}",
                tags=["request", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error creating fix request: {str(e)}",
                tags=["request", "error"]
            ) 