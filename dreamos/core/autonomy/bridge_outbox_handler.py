"""
Bridge Outbox Handler
-------------------
Processes agent responses and applies code changes:
1. Parses GPT agent responses
2. Applies code edits using AST
3. Moves files if renamed
4. Auto-validates with pytest
5. Commits changes if tests pass
"""

import ast
import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from ..logging.log_manager import LogManager
from ..agent_loop import AgentLoop

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeOutboxHandler:
    """Processes agent responses and applies code changes."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the bridge outbox handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LogManager()
        self.agent_loop = AgentLoop()
        
        # Default configuration
        self.check_interval = self.config.get("check_interval", 5)  # 5 seconds
        self.max_retries = self.config.get("max_retries", 3)
        self.commit_message_template = self.config.get(
            "commit_message_template",
            "Agent-X fix: {description}"
        )
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.processed_responses = set()
        
        # Initialize logging
        self.logger.info(
            platform="bridge_outbox",
            status="initialized",
            message="Bridge outbox handler initialized",
            tags=["init", "outbox"]
        )
    
    async def start(self):
        """Start the outbox handler."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform="bridge_outbox",
            status="started",
            message="Bridge outbox handler started",
            tags=["start", "outbox"]
        )
    
    async def stop(self):
        """Stop the outbox handler."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            platform="bridge_outbox",
            status="stopped",
            message="Bridge outbox handler stopped",
            tags=["stop", "outbox"]
        )
    
    async def _process_response(self, response: Dict[str, Any]):
        """Process an agent response.
        
        Args:
            response: Agent response dictionary
        """
        try:
            content = response.get("content", "")
            if not content:
                return
            
            # Parse code changes
            changes = self._parse_code_changes(content)
            if not changes:
                return
            
            # Apply changes
            for file_path, code_changes in changes.items():
                await self._apply_file_changes(file_path, code_changes)
            
            # Run tests
            if await self._run_tests():
                # Commit changes
                await self._commit_changes(response)
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error processing response: {str(e)}",
                tags=["process", "error"]
            )
    
    def _parse_code_changes(self, content: str) -> Dict[str, str]:
        """Parse code changes from agent response.
        
        Args:
            content: Agent response content
            
        Returns:
            Dictionary mapping file paths to code changes
        """
        changes = {}
        current_file = None
        code_buffer = []
        
        for line in content.split('\n'):
            if line.startswith('# File:'):
                if current_file and code_buffer:
                    changes[current_file] = '\n'.join(code_buffer)
                current_file = line.split(':', 1)[1].strip()
                code_buffer = []
            elif current_file and line.strip():
                code_buffer.append(line)
        
        if current_file and code_buffer:
            changes[current_file] = '\n'.join(code_buffer)
        
        return changes
    
    async def _apply_file_changes(self, file_path: str, changes: str):
        """Apply code changes to a file using AST.
        
        Args:
            file_path: Path to file to modify
            changes: Code changes to apply
        """
        try:
            # Parse original file
            with open(file_path, 'r') as f:
                original_content = f.read()
                original_ast = ast.parse(original_content)
            
            # Parse changes
            changes_ast = ast.parse(changes)
            
            # Apply changes
            new_content = self._apply_ast_changes(original_ast, changes_ast)
            
            # Write changes
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            self.logger.info(
                platform="bridge_outbox",
                status="success",
                message=f"Applied changes to {file_path}",
                tags=["fix", "apply"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error applying changes to {file_path}: {str(e)}",
                tags=["fix", "error"]
            )
            raise
    
    def _apply_ast_changes(self, original_ast: ast.AST, changes_ast: ast.AST) -> str:
        """Apply AST changes to original code.
        
        Args:
            original_ast: Original code AST
            changes_ast: Changes AST
            
        Returns:
            Modified code as string
        """
        # TODO: Implement AST-based changes
        # For now, just return the changes
        return ast.unparse(changes_ast)
    
    async def _run_tests(self) -> bool:
        """Run tests to validate changes.
        
        Returns:
            True if tests pass
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "pytest",
                "-v",
                "--tb=short",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                self.logger.info(
                    platform="bridge_outbox",
                    status="success",
                    message="Tests passed",
                    tags=["test", "success"]
                )
                return True
            else:
                self.logger.warning(
                    platform="bridge_outbox",
                    status="warning",
                    message="Tests failed",
                    tags=["test", "failure"]
                )
                return False
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error running tests: {str(e)}",
                tags=["test", "error"]
            )
            return False
    
    async def _commit_changes(self, response: Dict[str, Any]):
        """Commit code changes.
        
        Args:
            response: Agent response dictionary
        """
        try:
            # Extract description from response
            content = response.get("content", "")
            description = content.split('\n\n')[-1].strip()
            if len(description) > 100:
                description = description[:97] + "..."
            
            # Create commit message
            commit_msg = self.commit_message_template.format(
                description=description
            )
            
            # Run git commit
            process = await asyncio.create_subprocess_exec(
                "git",
                "add",
                ".",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            process = await asyncio.create_subprocess_exec(
                "git",
                "commit",
                "-m",
                commit_msg,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            self.logger.info(
                platform="bridge_outbox",
                status="success",
                message=f"Committed changes: {commit_msg}",
                tags=["commit", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="bridge_outbox",
                status="error",
                message=f"Error committing changes: {str(e)}",
                tags=["commit", "error"]
            )
            raise
    
    async def _worker_loop(self):
        """Main worker loop for outbox handler."""
        while self.is_running:
            try:
                # Check for new responses
                responses = await self.agent_loop._load_inbox("autonomy_agent")
                
                for response in responses:
                    response_id = response.get("id")
                    if response_id and response_id not in self.processed_responses:
                        await self._process_response(response)
                        self.processed_responses.add(response_id)
                
                # Small sleep to prevent CPU spinning
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    platform="bridge_outbox",
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["worker", "error"]
                )
                await asyncio.sleep(5)  # Back off on error 