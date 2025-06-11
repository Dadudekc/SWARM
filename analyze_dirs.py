"""
Analyze directory structure for potential issues.
"""

import os
from pathlib import Path
import sys

def analyze_directory(root_dir: str, max_depth: int = 10):
    """Analyze directory structure for potential issues.
    
    Args:
        root_dir: Root directory to analyze
        max_depth: Maximum directory depth to check
    """
    root = Path(root_dir)
    visited = set()
    deep_dirs = []
    symlinks = []
    
    print(f"Analyzing directory: {root_dir}")
    print("-" * 80)
    
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            path = Path(dirpath)
            
            # Check depth
            depth = len(path.relative_to(root).parts)
            if depth > max_depth:
                deep_dirs.append(str(path))
                continue
                
            # Check for symlinks
            for dirname in dirnames:
                full_path = path / dirname
                if full_path.is_symlink():
                    symlinks.append(str(full_path))
                    
            # Track visited paths
            path_str = str(path)
            if path_str in visited:
                print(f"Warning: Circular reference detected at {path_str}")
            visited.add(path_str)
            
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        
    # Print results
    if deep_dirs:
        print("\nDeep directories (>10 levels):")
        for d in deep_dirs:
            print(f"  {d}")
            
    if symlinks:
        print("\nSymlinks found:")
        for s in symlinks:
            print(f"  {s}")
            
    print(f"\nTotal directories analyzed: {len(visited)}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        analyze_directory(sys.argv[1])
    else:
        analyze_directory('dreamos') 