"""
Initialize the test feedback loop with current test status.
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from .test_feedback import TestFeedbackLoop, TestError, AgentStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_pytest() -> Dict[str, Any]:
    """Run pytest and collect results."""
    cmd = ["pytest", "-n", "auto", "--lf", "--maxfail=10", "--tb=short"]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        return {
            'exit_code': process.returncode,
            'stdout': stdout.decode(),
            'stderr': stderr.decode()
        }
    except Exception as e:
        logger.error(f"Error running pytest: {e}")
        return {
            'exit_code': -1,
            'stdout': '',
            'stderr': str(e)
        }

def parse_test_output(output: str) -> List[Dict[str, Any]]:
    """Parse pytest output to extract test results."""
    results = []
    current_test = None
    
    for line in output.split('\n'):
        if line.startswith('tests/'):
            # New test found
            if current_test:
                results.append(current_test)
            current_test = {
                'file': line.split('::')[0],
                'name': line.split('::')[-1],
                'status': 'unknown',
                'error': None
            }
        elif current_test and line.strip():
            if 'FAILED' in line:
                current_test['status'] = 'failed'
            elif 'ERROR' in line:
                current_test['status'] = 'error'
            elif 'PASSED' in line:
                current_test['status'] = 'passed'
            elif 'SKIPPED' in line:
                current_test['status'] = 'skipped'
            elif current_test['status'] in ['failed', 'error']:
                current_test['error'] = line.strip()
    
    if current_test:
        results.append(current_test)
    
    return results

def initialize_agent_assignments() -> Dict[str, Dict[str, Any]]:
    """Initialize agent assignments based on current test status."""
    return {
        'agent1': {
            'focus': 'Windows Permissions & ACL',
            'priority': 'high',
            'current_task': 'Fixing PermissionError issues',
            'files': [
                'tests/social/core/test_log_manager.py',
                'tests/social/core/test_log_metrics.py'
            ],
            'tasks': [
                'Fix directory cleanup failures',
                'Implement proper Windows ACL handling'
            ],
            'last_update': datetime.now().isoformat(),
            'status': 'active'
        },
        'agent2': {
            'focus': 'LogManager Core',
            'priority': 'high',
            'current_task': 'Fixing initialization issues',
            'files': [
                'tests/social/core/test_log_manager.py',
                'tests/social/core/test_log_metrics.py'
            ],
            'tasks': [
                'Fix LogManager initialization',
                'Resolve argument handling issues'
            ],
            'last_update': datetime.now().isoformat(),
            'status': 'active'
        },
        'agent3': {
            'focus': 'Reddit Strategy',
            'priority': 'medium',
            'current_task': 'Fixing authentication issues',
            'files': [
                'tests/social/strategies/reddit/test_post_handler.py',
                'tests/social/strategies/reddit/test_reddit_strategy.py'
            ],
            'tasks': [
                'Fix browser configuration',
                'Implement session validation'
            ],
            'last_update': datetime.now().isoformat(),
            'status': 'active'
        },
        'agent4': {
            'focus': 'Test Infrastructure',
            'priority': 'medium',
            'current_task': 'Fixing test fixtures',
            'files': [
                'tests/conftest.py',
                'tests/utils/test_utils.py'
            ],
            'tasks': [
                'Add missing batcher fixture',
                'Improve test isolation'
            ],
            'last_update': datetime.now().isoformat(),
            'status': 'active'
        }
    }

async def main():
    """Initialize the feedback loop with current test status."""
    # Create feedback loop
    feedback_loop = TestFeedbackLoop()
    
    # Run tests
    test_results = await run_pytest()
    if test_results['exit_code'] == -1:
        logger.error("Failed to run tests")
        return
    
    # Parse test results
    results = parse_test_output(test_results['stdout'])
    
    # Initialize agent assignments
    agent_assignments = initialize_agent_assignments()
    for agent_id, status in agent_assignments.items():
        feedback_loop.update_agent_status(agent_id, status)
    
    # Record errors
    for result in results:
        if result['status'] in ['failed', 'error']:
            error = TestError(
                file=result['file'],
                error=result['error'] or 'Unknown error',
                suggested_fix='To be determined',
                status='new',
                priority='high' if 'PermissionError' in str(result['error']) else 'medium',
                discovered_at=datetime.now().isoformat()
            )
            feedback_loop.record_error(error)
    
    logger.info("Feedback loop initialized successfully")

if __name__ == '__main__':
    asyncio.run(main()) 