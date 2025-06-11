"""
Run the scanner on the dreamos directory with verbose logging.
"""

import asyncio
import logging
from pathlib import Path
from agent_tools.swarm_tools.scanner.scanner import Scanner
import time

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more verbose output
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        start_time = time.time()
        # Initialize scanner with dreamos directory
        logger.debug("About to initialize scanner...")
        scanner = Scanner('dreamos')
        logger.debug("Scanner initialized successfully")
        
        # Run scan with timeout
        logger.debug("Starting scan operation...")
        try:
            # Set a 30 second timeout for the scan
            results = await asyncio.wait_for(scanner.scan(), timeout=30.0)
            logger.debug("Scan operation completed. Results: %s", results)
        except asyncio.TimeoutError:
            logger.error("Scan operation timed out after 30 seconds")
            print("\n❌ Scan timed out after 30 seconds")
            return
        
        elapsed_time = time.time() - start_time
        logger.info(f"Total scan time: {elapsed_time:.2f} seconds")
        
        # Print summary
        logger.info("Scan complete. Results:")
        print("\nScan Results:")
        print(results.summary())
        
        # Check for output files
        output_files = {
            'project_analysis.json': Path('project_analysis.json'),
            'chatgpt_project_context.json': Path('chatgpt_project_context.json')
        }
        
        print("\nOutput File Status:")
        for filename, path in output_files.items():
            if path.exists():
                size = path.stat().st_size / 1024  # Convert to KB
                print(f"✅ {filename} created ({size:.1f} KB)")
            else:
                print(f"⚠️ {filename} not found")
        
        print("\n✅ Project scan finished successfully.")
        
    except Exception as e:
        logger.error(f"Error during scan: {str(e)}", exc_info=True)
        print(f"\n❌ Scan failed: {str(e)}")
        raise  # Re-raise to ensure non-zero exit code

if __name__ == '__main__':
    asyncio.run(main()) 