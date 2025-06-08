"""
Run Response Loop
--------------
Script to run the response loop daemon.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

from .response_loop_daemon import ResponseLoopDaemon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    """Run the response loop daemon."""
    try:
        # Load configuration
        config_path = Path(os.getenv("RESPONSE_LOOP_CONFIG", "config/response_loop_config.json"))
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
            
        with open(config_path) as f:
            config = json.load(f)
        
        # Create and run daemon
        await ResponseLoopDaemon.create_and_run(config)
        
    except Exception as e:
        logger.error(f"Error running daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 