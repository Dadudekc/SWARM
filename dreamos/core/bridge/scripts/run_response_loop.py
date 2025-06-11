"""
Run Response Loop Daemon
---------------------
Script to run the response loop daemon.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

from ..response_loop_daemon import ResponseLoopDaemon

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main entry point."""
    try:
        # Get config path from environment or use default
        config_path = os.getenv(
            "RESPONSE_LOOP_CONFIG",
            str(Path(__file__).parent.parent.parent / "config" / "response_loop_config.json")
        )
        
        # Get Discord token from environment
        discord_token = os.getenv("DISCORD_TOKEN")
        
        # Create and start daemon
        daemon = ResponseLoopDaemon(config_path, discord_token)
        await daemon.start()
        
        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            await daemon.stop()
            
    except Exception as e:
        logger.error(f"Error running response loop daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 