import os
from pathlib import Path
import logging
from collections import defaultdict
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

def analyze_directory_structure(root_dir: str, max_depth: int = 5):
    """
    Analyze directory structure and identify problematic paths.
    """
    root_path = Path(root_dir)
    if not root_path.exists():
        logger.error(f"Root directory {root_dir} does not exist!")
        return

    # Track directory depths and repeated patterns
    deep_dirs = []
    repeated_patterns = defaultdict(list)
    symlinks = []
    
    def check_path(path: Path, current_depth: int = 0, path_components: list = None):
        if path_components is None:
            path_components = []
            
        try:
            # Check if it's a symlink
            if path.is_symlink():
                symlinks.append(str(path))
                return
                
            # Check depth
            if current_depth > max_depth:
                deep_dirs.append((str(path), current_depth))
                
            # Check for repeated patterns in path
            components = path.parts
            for i in range(len(components)):
                for j in range(i + 1, len(components)):
                    if components[i] == components[j]:
                        pattern = components[i]
                        repeated_patterns[pattern].append(str(path))
            
            # Recursively check subdirectories
            if path.is_dir():
                for child in path.iterdir():
                    if child.is_dir():
                        check_path(child, current_depth + 1, path_components + [child.name])
                        
        except Exception as e:
            logger.error(f"Error processing {path}: {e}")

    logger.info(f"Starting analysis of {root_dir}")
    check_path(root_path)
    
    # Report findings
    if deep_dirs:
        logger.info("\n=== Deep Directories (depth > {}) ===".format(max_depth))
        for path, depth in sorted(deep_dirs, key=lambda x: x[1], reverse=True):
            logger.info(f"Depth {depth}: {path}")
            
    if repeated_patterns:
        logger.info("\n=== Repeated Directory Patterns ===")
        for pattern, paths in repeated_patterns.items():
            if len(paths) > 1:  # Only show if pattern appears multiple times
                logger.info(f"\nPattern '{pattern}' appears in:")
                for path in paths:
                    logger.info(f"  - {path}")
                    
    if symlinks:
        logger.info("\n=== Symlinks Found ===")
        for symlink in symlinks:
            logger.info(f"  - {symlink}")
            
    if not any([deep_dirs, repeated_patterns, symlinks]):
        logger.info("No problematic paths found!")

if __name__ == "__main__":
    tests_dir = "tests"
    analyze_directory_structure(tests_dir) 