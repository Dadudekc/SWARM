"""
Test Runner
---------
Runs tests for the unified handler implementation.
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

from tests.core.handlers.tests.test_handler import TestHandler

logger = logging.getLogger(__name__)

async def run_handler_tests() -> Dict[str, Any]:
    """Run all handler tests.
    
    Returns:
        Dict containing test results
    """
    results = {
        'success': False,
        'tests': [],
        'errors': []
    }
    
    try:
        # Create test handler
        handler = TestHandler()
        
        # Run tests
        test_success = await handler.run_tests()
        
        # Record results
        results['success'] = test_success
        results['tests'].append({
            'name': 'unified_handler',
            'success': test_success
        })
        
        if not test_success:
            results['errors'].append('Unified handler tests failed')
            
    except Exception as e:
        results['success'] = False
        results['errors'].append(f'Error running tests: {str(e)}')
        
    return results

def main():
    """Run tests and report results."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run tests
    results = asyncio.run(run_handler_tests())
    
    # Report results
    if results['success']:
        logger.info("All tests passed!")
    else:
        logger.error("Tests failed:")
        for error in results['errors']:
            logger.error(f"- {error}")
            
    return 0 if results['success'] else 1

if __name__ == '__main__':
    exit(main()) 