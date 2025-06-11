"""
Test File Mover

This script moves test files from the main codebase to the appropriate test directories.
"""

import os
import shutil
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_test_destination(source_path: Path) -> Path:
    """Get the appropriate test directory for a test file.
    
    Args:
        source_path: Path to the source test file
        
    Returns:
        Path to the destination test directory
    """
    # Get the relative path from dreamos/core
    try:
        rel_path = source_path.relative_to(Path("dreamos/core"))
    except ValueError:
        # If not in dreamos/core, use the parent directory name
        rel_path = source_path.parent.name
        
    # Create the destination path
    dest_dir = Path("tests") / rel_path
    return dest_dir

def move_test_file(source_path: Path) -> bool:
    """Move a test file to the appropriate test directory.
    
    Args:
        source_path: Path to the source test file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get destination directory
        dest_dir = get_test_destination(source_path)
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Get destination file path
        dest_path = dest_dir / source_path.name
        
        # Skip if file already exists
        if dest_path.exists():
            logger.warning(f"File already exists: {dest_path}")
            return False
            
        # Move the file
        shutil.move(str(source_path), str(dest_path))
        
        logger.info(f"Moved {source_path} to {dest_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error moving {source_path}: {e}")
        return False

def find_test_files(base_dir: Path) -> list[Path]:
    """Find all test files in the given directory.
    
    Args:
        base_dir: Base directory to search
        
    Returns:
        List of test file paths
    """
    test_files = []
    
    for path in base_dir.rglob("test_*.py"):
        # Skip files already in tests directory
        if "tests" in path.parts:
            continue
            
        test_files.append(path)
        
    return test_files

def main():
    """Main entry point."""
    # Get base directory
    base_dir = Path("dreamos")
    
    # Find test files
    test_files = find_test_files(base_dir)
    
    # Move test files
    moved = 0
    failed = 0
    skipped = 0
    
    for test_file in test_files:
        if move_test_file(test_file):
            moved += 1
        elif test_file.name in [p.name for p in Path("tests").rglob("test_*.py")]:
            skipped += 1
        else:
            failed += 1
            
    logger.info(f"Moved {moved} test files, {skipped} skipped (already exist), {failed} failed")

if __name__ == "__main__":
    main() 