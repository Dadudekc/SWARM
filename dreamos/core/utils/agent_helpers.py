"""
Agent Helpers
-----------
Essential utilities for agent operations and test management.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple, Union

from .core_utils import load_json, save_json, ensure_dir

logger = logging.getLogger(__name__)

# Agent Operations
def load_agent_ownership(ownership_file: str = "data/agent_ownership.json") -> Dict[str, List[str]]:
    """Load agent ownership data.
    
    Args:
        ownership_file: Path to ownership JSON file
        
    Returns:
        Dictionary mapping agents to owned files
    """
    return load_json(ownership_file, default={})

def determine_responsible_agent(
    file_path: Path,
    ownership_data: Dict[str, List[str]]
) -> str:
    """Determine which agent is responsible for a file.
    
    Args:
        file_path: Path to file
        ownership_data: Agent ownership data
        
    Returns:
        Agent identifier
    """
    try:
        file_str = str(file_path)
        for agent, files in ownership_data.items():
            if any(file_str.endswith(f) for f in files):
                return agent
        return "codex"
    except Exception as e:
        logger.error(f"Error determining responsible agent: {e}")
        return "codex"

def validate_agent_id(agent_id: str) -> bool:
    """Validate an agent ID format.
    
    Args:
        agent_id: Agent ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    return agent_id.startswith("Agent-")

def build_agent_message(
    agent_id: Union[str, List[str]],
    content: str,
    mode: str = "NORMAL"
) -> Dict[str, Any]:
    """Build a message dictionary for an agent.
    
    Args:
        agent_id: Single agent ID or list of agent IDs
        content: Message content
        mode: Message mode (NORMAL, VERIFY, etc.)
        
    Returns:
        Message dictionary
    """
    return {
        "to_agent": agent_id,
        "content": content,
        "mode": mode,
        "timestamp": time.time()
    }

# Test Operations
async def run_tests(
    test_dir: str = "tests",
    test_pattern: str = "test_*.py",
    max_workers: int = None,
    test_timeout: int = 300
) -> Tuple[bool, List[Dict[str, Any]]]:
    """Run tests and collect results.
    
    Args:
        test_dir: Directory containing tests
        test_pattern: Pattern to match test files
        max_workers: Maximum number of worker processes
        test_timeout: Test timeout in seconds
        
    Returns:
        Tuple of (success, test_results)
    """
    try:
        args = [
            "pytest",
            test_dir,
            "-v",
            f"--pattern={test_pattern}",
            "--json-report",
            f"--timeout={test_timeout}"
        ]
        
        if max_workers:
            args.extend(["-n", str(max_workers)])
        
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Tests failed: {stderr.decode()}")
            return False, []
        
        results = []
        for line in stdout.decode().splitlines():
            if line.startswith("{"):
                try:
                    result = json.loads(line)
                    results.append(result)
                except json.JSONDecodeError:
                    continue
        
        return True, results
        
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False, []

async def get_test_file(test_name: str) -> Optional[Path]:
    """Get the file path for a test.
    
    Args:
        test_name: Name of the test
        
    Returns:
        Path to test file if found, None otherwise
    """
    try:
        process = await asyncio.create_subprocess_exec(
            "pytest",
            "--collect-only",
            "-q",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"Error collecting tests: {stderr.decode()}")
            return None
        
        for line in stdout.decode().splitlines():
            if test_name in line:
                parts = line.split("::")
                if len(parts) >= 1:
                    return Path(parts[0])
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting test file: {e}")
        return None

def parse_test_failures(output: str) -> List[Dict[str, Any]]:
    """Parse test failures from pytest output.
    
    Args:
        output: Pytest output string
        
    Returns:
        List of test failure dictionaries
    """
    failures = []
    current_failure = None
    
    for line in output.splitlines():
        if line.startswith("FAILED"):
            if current_failure:
                failures.append(current_failure)
            current_failure = {
                "test_name": line.split()[1],
                "error": "",
                "traceback": []
            }
        elif current_failure:
            if line.strip():
                current_failure["traceback"].append(line)
            if "AssertionError" in line or "Exception" in line:
                current_failure["error"] = line
    
    if current_failure:
        failures.append(current_failure)
    
    return failures

def get_test_files(test_dir: str = "tests", pattern: str = "test_*.py") -> Set[str]:
    """Get all test files matching pattern.
    
    Args:
        test_dir: Directory containing tests
        pattern: Pattern to match test files
        
    Returns:
        Set of test file paths
    """
    try:
        test_path = Path(test_dir)
        return {
            str(f.relative_to(test_path))
            for f in test_path.glob(pattern)
            if f.is_file()
        }
    except Exception as e:
        logger.error(f"Error getting test files: {e}")
        return set() 
