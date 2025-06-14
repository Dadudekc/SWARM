#!/usr/bin/env python3
"""
Analyze the restructured dreamos directory.
This script helps verify the restructuring process by analyzing the new structure.
"""

import json
import logging
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set

# Constants
ROOT_DIR = Path("dreamos")
MOVE_MAP_FILE = ROOT_DIR / "file_move_map.json"

def load_move_map() -> Dict[str, str]:
    """Load the file move map."""
    with open(MOVE_MAP_FILE, "r") as f:
        return json.load(f)

def analyze_structure():
    """Analyze the new directory structure."""
    base_path = Path("dreamos")
    
    # Get all Python files
    python_files = list(base_path.rglob("*.py"))
    
    # Analyze imports
    import_map = {}
    for file in python_files:
        with open(file, "r") as f:
            content = f.read()
            # Find all imports
            imports = re.findall(r"from\s+([\w.]+)\s+import", content)
            import_map[file] = imports
    
    return import_map

def analyze_directory(base_path: Path) -> Dict[str, int]:
    """Analyze directory structure and file counts."""
    stats = defaultdict(int)
    for path in base_path.rglob("*"):
        if path.is_file():
            # Count files by top-level directory
            rel_path = path.relative_to(base_path)
            top_dir = rel_path.parts[0]
            stats[top_dir] += 1
    return dict(stats)

def generate_tree(base_path: Path, prefix: str = "", is_last: bool = True) -> str:
    """Generate a pretty directory tree."""
    result = []
    
    # Get all items in current directory
    items = sorted(base_path.iterdir())
    dirs = [item for item in items if item.is_dir()]
    files = [item for item in items if item.is_file()]
    
    # Print directories first
    for i, dir_path in enumerate(dirs):
        is_last_dir = i == len(dirs) - 1 and not files
        new_prefix = prefix + ("    " if is_last else "│   ")
        result.append(f"{prefix}{'└── ' if is_last_dir else '├── '}{dir_path.name}/")
        result.append(generate_tree(dir_path, new_prefix, is_last_dir))
    
    # Print files
    for i, file_path in enumerate(files):
        is_last_file = i == len(files) - 1
        result.append(f"{prefix}{'└── ' if is_last_file else '├── '}{file_path.name}")
    
    return "\n".join(result)

def main():
    """Main execution function."""
    base_path = Path("dreamos")
    
    # Load move map
    move_map = load_move_map()
    
    # Analyze directory structure
    stats = analyze_directory(base_path)
    
    # Print summary
    print("\n=== Directory Structure Summary ===")
    print(f"Total files: {sum(stats.values())}")
    print("\nFiles by top-level directory:")
    for dir_name, count in sorted(stats.items()):
        print(f"  {dir_name}: {count} files")
    
    # Print move map summary
    print("\n=== Move Map Summary ===")
    print(f"Total moves: {len(move_map)}")
    print("\nMoves by category:")
    categories = defaultdict(int)
    for src, dst in move_map.items():
        category = dst.split("/")[0]
        categories[category] += 1
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count} files")
    
    # Generate and print tree
    print("\n=== Directory Tree ===")
    print(generate_tree(base_path))

if __name__ == "__main__":
    main() 