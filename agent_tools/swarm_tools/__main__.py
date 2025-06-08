import argparse
import asyncio
import logging
from pathlib import Path
from typing import List, Optional

from agent_tools.scanner.scanner import Scanner

def main():
    """Main entry point for the project scanner."""
    parser = argparse.ArgumentParser(description="Scan project and generate documentation")
    parser.add_argument("--project-root", default=".", help="Root directory of the project")
    parser.add_argument("--ignore", help="Comma-separated list of directories to ignore")
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse ignore patterns
    ignore_patterns = args.ignore.split(",") if args.ignore else None
    
    # Initialize scanner
    scanner = Scanner(args.project_root)
    
    # Run async scan
    async def run_scan():
        await scanner.scan_project(ignore_patterns)
    
    # Run the async scan
    asyncio.run(run_scan())

if __name__ == "__main__":
    main() 
