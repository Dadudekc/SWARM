"""
Autonomy Loop Runner

Core loop that detects test failures, generates prompts, injects them into agents,
validates fixes, and escalates to Codex if needed.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pyautogui
import pytest
import os
import sys
import logging

from .utils.file_utils import (
    safe_read,
    safe_write,
    ensure_dir,
)
from .utils.json_utils import (
    load_json,
    save_json,
)
from social.utils.log_manager import LogManager, LogConfig, LogLevel

# Initialize logging
log_manager = LogManager(LogConfig(
    level=LogLevel.INFO,
    log_dir="logs",
    platforms={"autonomy": "autonomy.log"}
))
logger = log_manager

class AutonomyLoopRunner:
    def __init__(self, config_path: str = "config/autonomy_config.json"):
        """Initialize the autonomy loop runner.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.agent_ownership = self._load_agent_ownership()
        self.codex_agent = "codex"  # Special agent for quality control
        self.bridge_outbox = Path("bridge_outbox")
        ensure_dir(self.bridge_outbox)
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        try:
            return load_json(config_path, default={})
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
            
    def _load_agent_ownership(self) -> Dict[str, str]:
        """Load agent ownership mapping."""
        try:
            return load_json("config/agent_ownership.json", default={})
        except Exception as e:
            logger.error(f"Error loading agent ownership: {e}")
            return {}
            
    async def run_pytest_and_parse_failures(self) -> List[Dict]:
        """Run pytest and parse failures.
        
        Returns:
            List of test failures with details
        """
        cmd = ["pytest", "-n", "auto", "--lf", "--maxfail=10", "--tb=short", "--json-report"]
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # Parse JSON report
                report_path = Path(".report.json")
                if report_path.exists():
                    with open(report_path, 'r') as f:
                        report = json.load(f)
                        return self._parse_test_failures(report)
                        
            return []
            
        except Exception as e:
            logger.error(f"Error running pytest: {e}")
            return []
            
    def _parse_test_failures(self, report: Dict) -> List[Dict]:
        """Parse test failures from pytest report."""
        failures = []
        for test in report.get("tests", []):
            if test.get("outcome") == "failed":
                failures.append({
                    "file": test.get("file"),
                    "name": test.get("name"),
                    "error": test.get("call", {}).get("longrepr"),
                    "traceback": test.get("call", {}).get("traceback")
                })
        return failures
        
    def determine_responsible_agent(self, file_path: str) -> str:
        """Determine which agent is responsible for a file."""
        # Check ownership map first
        if file_path in self.agent_ownership:
            return self.agent_ownership[file_path]
            
        # Fallback to file prefix
        prefix = file_path.split("/")[0]
        if prefix in self.agent_ownership:
            return self.agent_ownership[prefix]
            
        # Default to agent-4 for unknown files
        return "agent4"
        
    def generate_fix_prompt(self, test: Dict) -> str:
        """Generate a fix prompt for an agent."""
        return f"""
You're Agent-{self.determine_responsible_agent(test['file'])}. Your task is to fix the following test failure in `{test['file']}`:

- ❌ Test Name: {test['name']}
- 🧪 Error: {test['error']}
- 📄 File: {test['file']}
- 📜 Traceback:
{test['traceback']}

Focus only on the relevant file. Return the fixed code.
"""
        
    async def inject_prompt_to_agent(self, agent_id: str, prompt: str):
        """Inject a prompt into an agent's input field."""
        try:
            # Save prompt to bridge outbox
            prompt_file = self.bridge_outbox / f"agent-{agent_id}.json"
            save_json({
                "prompt": prompt,
                "timestamp": datetime.utcnow().isoformat()
            }, prompt_file)
                
            # Use PyAutoGUI to type prompt
            # Note: This assumes the agent's input field is focused
            pyautogui.write(prompt)
            pyautogui.press('enter')
            
        except Exception as e:
            logger.error(f"Error injecting prompt to agent {agent_id}: {e}")
            
    async def wait_for_reply(self, agent_id: str, timeout: int = 300) -> bool:
        """Wait for agent reply with timeout."""
        start_time = datetime.utcnow()
        while (datetime.utcnow() - start_time).seconds < timeout:
            response_file = self.bridge_outbox / f"agent-{agent_id}-response.json"
            if response_file.exists():
                return True
            await asyncio.sleep(1)
        return False
        
    def retrieve_response(self, agent_id: str) -> Optional[str]:
        """Retrieve agent's response."""
        try:
            response_file = self.bridge_outbox / f"agent-{agent_id}-response.json"
            if response_file.exists():
                data = load_json(response_file)
                return data.get("response") if data else None
        except Exception as e:
            logger.error(f"Error retrieving response from agent {agent_id}: {e}")
        return None
        
    async def is_valid_code(self, response: str) -> bool:
        """Check if code is valid using Codex."""
        try:
            # Ask Codex to validate
            prompt = f"Does this code look valid?\n{response}"
            await self.inject_prompt_to_agent(self.codex_agent, prompt)
            
            if await self.wait_for_reply(self.codex_agent):
                codex_response = self.retrieve_response(self.codex_agent)
                return codex_response and "valid" in codex_response.lower()
                
        except Exception as e:
            logger.error(f"Error validating code with Codex: {e}")
        return False
        
    def apply_code_patch(self, file_path: str, response: str) -> bool:
        """Apply code patch to file."""
        try:
            return safe_write(file_path, response)
        except Exception as e:
            logger.error(f"Error applying code patch to {file_path}: {e}")
            return False
            
    async def test_passes(self, file_path: str) -> bool:
        """Check if tests pass after patch."""
        try:
            cmd = ["pytest", file_path, "-v"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return process.returncode == 0
        except Exception as e:
            logger.error(f"Error running tests for {file_path}: {e}")
            return False
            
    async def escalate_to_codex(self, agent_id: str, file_path: str, test: Dict, response: str):
        """Escalate failed fix to Codex."""
        prompt = f"""
Agent-{agent_id} attempted to fix {test['name']} in {file_path} but failed.
Here's the bad code:
{response}

Can you produce a corrected version that will pass the test?
"""
        await self.inject_prompt_to_agent(self.codex_agent, prompt)
        
    def commit_code(self, file_path: str, message: str):
        """Commit code changes."""
        try:
            import subprocess
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run(["git", "commit", "-m", message], check=True)
        except Exception as e:
            logger.error(f"Error committing code: {e}")
            
    async def run_loop(self):
        """Main autonomy loop."""
        while True:
            try:
                failed_tests = await self.run_pytest_and_parse_failures()
                
                for test in failed_tests:
                    file_path = test["file"]
                    agent_id = self.determine_responsible_agent(file_path)
                    
                    prompt = self.generate_fix_prompt(test)
                    await self.inject_prompt_to_agent(agent_id, prompt)
                    
                    if not await self.wait_for_reply(agent_id):
                        logger.warning(f"Timeout waiting for agent {agent_id}")
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
                await asyncio.sleep(self.config.get("interval_seconds", 300))
                
            except Exception as e:
                logger.error(f"Error in autonomy loop: {e}")
                await asyncio.sleep(60)  # Sleep on error
                
if __name__ == "__main__":
    runner = AutonomyLoopRunner()
    asyncio.run(runner.run_loop()) 