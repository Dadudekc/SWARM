"""
Base Handler
-----------
Base class for all handlers with common functionality.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from ..logging.log_manager import LogManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all handlers with common functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the base handler.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = LogManager()
        
        # Default configuration
        self.check_interval = self.config.get("check_interval", 5)  # 5 seconds
        self.max_retries = self.config.get("max_retries", 3)
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.processed_items: Set[str] = set()
        
        # Initialize logging
        self.logger.info(
            platform=self.__class__.__name__.lower(),
            status="initialized",
            message=f"{self.__class__.__name__} initialized",
            tags=["init"]
        )
    
    async def start(self):
        """Start the handler."""
        if self.is_running:
            return
            
        self.is_running = True
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform=self.__class__.__name__.lower(),
            status="started",
            message=f"{self.__class__.__name__} started",
            tags=["start"]
        )
    
    async def stop(self):
        """Stop the handler."""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            platform=self.__class__.__name__.lower(),
            status="stopped",
            message=f"{self.__class__.__name__} stopped",
            tags=["stop"]
        )
    
    async def _worker_loop(self):
        """Main worker loop for handler."""
        while self.is_running:
            try:
                await self._process_items()
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    platform=self.__class__.__name__.lower(),
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["worker", "error"]
                )
                await asyncio.sleep(5)  # Back off on error
    
    async def _process_items(self):
        """Process items in the handler. Override in subclasses."""
        raise NotImplementedError
    
    async def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON data from file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Loaded JSON data
        """
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(
                platform=self.__class__.__name__.lower(),
                status="error",
                message=f"Error loading JSON from {file_path}: {str(e)}",
                tags=["json", "error"]
            )
            return {}
    
    async def _save_json(self, file_path: str, data: Dict[str, Any]):
        """Save JSON data to file.
        
        Args:
            file_path: Path to JSON file
            data: Data to save
        """
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            self.logger.error(
                platform=self.__class__.__name__.lower(),
                status="error",
                message=f"Error saving JSON to {file_path}: {str(e)}",
                tags=["json", "error"]
            )
    
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
                    platform=self.__class__.__name__.lower(),
                    status="success",
                    message="Tests passed",
                    tags=["test", "success"]
                )
                return True
            else:
                self.logger.warning(
                    platform=self.__class__.__name__.lower(),
                    status="warning",
                    message="Tests failed",
                    tags=["test", "failure"]
                )
                return False
            
        except Exception as e:
            self.logger.error(
                platform=self.__class__.__name__.lower(),
                status="error",
                message=f"Error running tests: {str(e)}",
                tags=["test", "error"]
            )
            return False 
