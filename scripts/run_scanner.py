#!/usr/bin/env python3
"""
Standalone script to run the Dream.OS code scanner.
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dreamos.core.verification.scanner import Scanner

def main():
    """Run the scanner on the project."""
    try:
        # Create scanner instance
        scanner = Scanner(str(project_root))
        
        # Run scan
        results = scanner.scan_project()
        
        # Print summary
        print("\nScan Summary:")
        print(f"Total Files: {results.total_files}")
        print(f"Total Duplicates: {results.total_duplicates}")
        print(f"Scan Time: {results.scan_time:.2f}s")
        
        if results.top_violators:
            print("\nTop Violators:")
            for violator in results.top_violators:
                print(f"- {violator['file']}: {violator['count']} duplicates")
        
        print("\nDetailed findings saved to reports/")
        
    except Exception as e:
        print(f"Error running scanner: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 