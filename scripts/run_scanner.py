#!/usr/bin/env python3
"""
Standalone script to run the Dream.OS code scanner.
"""

import sys
import os
import asyncio
from pathlib import Path
from tqdm import tqdm

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dreamos.core.verification.scanner import Scanner

def progress_callback(message: str, progress: float):
    """Update progress bar."""
    if not hasattr(progress_callback, 'pbar'):
        progress_callback.pbar = tqdm(total=100, desc="Scanning", unit="%")
    progress_callback.pbar.n = int(progress * 100)
    progress_callback.pbar.set_description(message)
    progress_callback.pbar.refresh()

async def main():
    """Run the scanner on the project."""
    try:
        # Create scanner instance with progress callback
        scanner = Scanner(str(project_root), progress_callback=progress_callback)
        
        # Run scan
        results = await scanner.scan_project()
        
        # Close progress bar
        if hasattr(progress_callback, 'pbar'):
            progress_callback.pbar.close()
        
        # Print summary
        print("\nScan Summary:")
        print(f"Total Files: {results.total_files}")
        print(f"Total Duplicates: {results.total_duplicates}")
        print(f"Scan Time: {results.scan_time:.2f}s")
        print(f"Errors: {len(results.errors)}")
        
        if results.top_violators:
            print("\nTop Violators:")
            for violator in results.top_violators:
                print(f"- {violator['file']}: {violator['count']} duplicates")
        
        if results.errors:
            print("\nErrors:")
            for error in results.errors:
                print(f"- {error['file']}: {error['error']}")
        
        # Save reports
        if results.save_reports():
            print("\nDetailed findings saved to reports/")
        else:
            print("\nError saving reports", file=sys.stderr)
        
    except Exception as e:
        print(f"Error running scanner: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 