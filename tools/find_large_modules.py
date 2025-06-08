#!/usr/bin/env python3
"""
Module Size Monitor
------------------
Scans Python modules for size violations and enforces limits.
Use with --fail-on-hit to fail CI on oversized modules.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse

def scan_modules(
    base: str = "dreamos/",
    limit: int = 300,
    exclude_patterns: Optional[List[str]] = None
) -> List[Tuple[Path, int]]:
    """Scan modules for size violations.
    
    Args:
        base: Base directory to scan
        limit: Maximum lines of code allowed
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        List of (path, line_count) tuples for oversized modules
    """
    oversized = []
    exclude_patterns = exclude_patterns or []
    
    for path in Path(base).rglob("*.py"):
        # Skip excluded patterns
        if any(path.match(pattern) for pattern in exclude_patterns):
            continue
            
        # Skip __init__.py and other special files
        if path.name.startswith("__"):
            continue
            
        # Count lines
        try:
            lines = path.read_text(encoding="utf-8").count("\n")
            if lines > limit:
                oversized.append((path, lines))
        except Exception as e:
            print(f"[!] Error reading {path}: {e}", file=sys.stderr)
            
    return sorted(oversized, key=lambda x: x[1], reverse=True)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Monitor module sizes")
    parser.add_argument(
        "--base",
        default="dreamos/",
        help="Base directory to scan"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=300,
        help="Maximum lines of code allowed"
    )
    parser.add_argument(
        "--fail-on-hit",
        action="store_true",
        help="Exit with error if oversized modules found"
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        help="Glob patterns to exclude"
    )
    args = parser.parse_args()
    
    # Scan for oversized modules
    oversized = scan_modules(
        base=args.base,
        limit=args.limit,
        exclude_patterns=args.exclude
    )
    
    # Report results
    if oversized:
        print(f"\n[!] Found {len(oversized)} oversized modules:")
        for path, lines in oversized:
            print(f"  - {path} ({lines} LOC)")
            
        if args.fail_on_hit:
            sys.exit(1)
    else:
        print("[✓] No oversized modules found")

if __name__ == "__main__":
    main() 