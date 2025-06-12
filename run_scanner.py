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
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        start_time = time.time()
        logger.debug("About to initialize scanner...")
        scanner = Scanner('dreamos')
        logger.debug("Scanner initialized successfully")
        
        # Run scan
        logger.debug("Starting scan operation...")
        print("\nStarting project scan...")
        results = await scanner.scan(categorize_agents=True, generate_init=True)
        print("\n")  # New line after progress
        
        elapsed_time = time.time() - start_time
        logger.info(f"Total scan time: {elapsed_time:.2f} seconds")
        
        # Save results
        if scanner.save_results(results):
            print("\n✅ Scan completed successfully")
            print("\nScan Results Summary:")
            print(results["narrative"])
        else:
            print("\n❌ Error saving scan results")
            return 1
        
        # Check for output files
        output_files = {
            'project_analysis.json': Path('dreamos/reports/project_analysis.json'),
            'chatgpt_project_context.json': Path('dreamos/reports/chatgpt_project_context.json')
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