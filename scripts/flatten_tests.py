import os
import shutil
from pathlib import Path
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def flatten_test_directory(root_dir: str):
    """
    Flatten the test directory structure by moving all test files to the root level.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        logger.error(f"Root directory {root_dir} does not exist!")
        return
    
    logger.info(f"Starting to flatten test directory: {root_dir}")
    test_files = []
    
    # Find all test files
    for path in root_path.rglob("test_*.py"):
        if path.parent != root_path:  # Skip files already in root
            test_files.append(path)
            logger.info(f"Found test file: {path}")
    
    logger.info(f"Found {len(test_files)} test files to move")
    
    # Move files to root
    moved_count = 0
    for test_file in test_files:
        new_name = test_file.name
        target_path = root_path / new_name
        
        # Handle naming conflicts
        counter = 1
        while target_path.exists():
            base_name = test_file.stem
            new_name = f"{base_name}_{counter}.py"
            target_path = root_path / new_name
            counter += 1
        
        try:
            shutil.move(str(test_file), str(target_path))
            moved_count += 1
            logger.info(f"Moved {test_file} to {target_path}")
        except Exception as e:
            logger.error(f"Failed to move {test_file}: {e}")
    
    logger.info(f"Successfully moved {moved_count} files")
    
    # Remove empty directories
    removed_count = 0
    for path in sorted(root_path.rglob("*"), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            try:
                path.rmdir()
                removed_count += 1
                logger.info(f"Removed empty directory: {path}")
            except Exception as e:
                logger.error(f"Failed to remove directory {path}: {e}")
    
    logger.info(f"Removed {removed_count} empty directories")

if __name__ == "__main__":
    tests_dir = "tests"
    logger.info("Starting test directory flattening process...")
    flatten_test_directory(tests_dir)
    logger.info("Test directory flattening process completed.") 