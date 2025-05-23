"""
Test runner for Discord bot tests.
"""

import asyncio
import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_discord_commands import TestHelpMenu, TestAgentCommands

def run_async_test(test_case):
    """Run an async test case."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_case)

def main():
    """Run all tests."""
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add HelpMenu tests
    suite.addTest(unittest.makeSuite(TestHelpMenu))
    
    # Add AgentCommands tests
    for test_name in dir(TestAgentCommands):
        if test_name.startswith('test_'):
            test_case = TestAgentCommands(test_name)
            suite.addTest(test_case)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return non-zero exit code if tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(main()) 