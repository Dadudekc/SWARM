"""
Autonomy Loop Runner
-------------------
Manages the autonomous test-fix loop by:
1. Running tests and detecting failures
2. Generating repair prompts
3. Injecting them into agent inboxes
4. Monitoring responses and applying fixes
5. Validating fixes and committing changes

Optimized for large-scale projects (3600+ files).
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import pyautogui
import pytest
from concurrent.futures import ThreadPoolExecutor

from ..logging.log_manager import LogManager
from ..messaging.chatgpt_bridge import ChatGPTBridge
from ..agent_loop import AgentLoop, start_agent_loops
from ...tests.utils.init_feedback_loop import run_pytest
from .test_devlog_bridge import TestDevLogBridge
from .devlog_manager import DevLogManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutonomyLoopRunner:
    """Manages the autonomous test-fix loop."""
    
    def __init__(self, config_path: str = "config/autonomy_config.json"):
        """Initialize the autonomy loop runner.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.agent_ownership = self._load_agent_ownership()
        self.codex_agent = "codex"  # Special agent for quality control
        self.bridge_outbox = Path("bridge_outbox")
        self.bridge_outbox.mkdir(exist_ok=True)
        
        # Initialize devlog components
        self.devlog_manager = DevLogManager()
        self.test_devlog_bridge = TestDevLogBridge(
            devlog_manager=self.devlog_manager,
            autonomy_runner=self
        )
        
        self.logger = LogManager()
        self.bridge = ChatGPTBridge(self.config)
        
        # Performance optimization settings
        self.max_workers = self.config.get("max_workers", os.cpu_count() or 4)
        self.chunk_size = self.config.get("chunk_size", 100)  # Files per chunk
        self.test_timeout = self.config.get("test_timeout", 300)  # 5 minutes per test
        self.max_concurrent_tests = self.config.get("max_concurrent_tests", 10)
        
        # Default configuration
        self.test_interval = self.config.get("test_interval", 300)  # 5 minutes
        self.max_retries = self.config.get("max_retries", 3)
        self.commit_message_template = self.config.get(
            "commit_message_template",
            "Agent-X fix: {description}"
        )
        
        # Runtime state
        self.is_running = False
        self.worker_task = None
        self.last_test_time = 0
        self.failed_tests = set()
        self.passed_tests = set()
        self.in_progress_tests = set()
        self.test_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        
        # Thread pool for parallel operations
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # Initialize logging
        self.logger.info(
            platform="autonomy_loop",
            status="initialized",
            message="Autonomy loop runner initialized",
            tags=["init", "autonomy"]
        )
    
    async def start(self):
        """Start the autonomy loop."""
        if self.is_running:
            return
            
        self.is_running = True
        
        # Start the agent loop in the background
        self.agent_loop_task = asyncio.create_task(start_agent_loops())
        
        # Start the main worker loop
        self.worker_task = asyncio.create_task(self._worker_loop())
        
        self.logger.info(
            platform="autonomy_loop",
            status="started",
            message="Autonomy loop started",
            tags=["start", "autonomy"]
        )
    
    async def stop(self):
        """Stop the autonomy loop."""
        self.is_running = False
        
        # Cancel both tasks
        if self.agent_loop_task:
            self.agent_loop_task.cancel()
            try:
                await self.agent_loop_task
            except asyncio.CancelledError:
                pass
                
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info(
            platform="autonomy_loop",
            status="stopped",
            message="Autonomy loop stopped",
            tags=["stop", "autonomy"]
        )
    
    async def _worker_loop(self):
        """Main worker loop that processes test failures."""
        while self.is_running:
            try:
                # Run tests and get failures
                failed_tests = await self.run_pytest_and_parse_failures()
                
                for test in failed_tests:
                    file_path = test["file"]
                    agent_id = self.determine_responsible_agent(file_path)
                    
                    prompt = self.generate_fix_prompt(test)
                    await self.inject_prompt_to_agent(agent_id, prompt)
                    
                    if not await self.wait_for_reply(agent_id):
                        self.logger.warning(
                            platform="autonomy_loop",
                            status="warning",
                            message=f"Timeout waiting for agent {agent_id}",
                            tags=["timeout", "warning"]
                        )
                        continue
                        
                    response = self.retrieve_response(agent_id)
                    if not response:
                        continue
                        
                    if not await self.is_valid_code(response):
                        await self.escalate_to_codex(agent_id, file_path, test, response)
                        continue
                        
                    if not self.apply_code_patch(file_path, response):
                        continue
                        
                    if not await self.test_passes(file_path):
                        await self.escalate_to_codex(agent_id, file_path, test, response)
                        continue
                        
                    self.commit_code(file_path, f"✅ Agent-{agent_id} fix for {test['name']}")
                
                # Sleep until next interval
                await asyncio.sleep(self.test_interval)
                
            except Exception as e:
                self.logger.error(
                    platform="autonomy_loop",
                    status="error",
                    message=f"Error in worker loop: {str(e)}",
                    tags=["error", "worker_loop"]
                )
                await asyncio.sleep(60)  # Sleep on error 