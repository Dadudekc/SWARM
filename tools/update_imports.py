#!/usr/bin/env python3
"""
Update imports in Python files based on the move map.
This script handles Phase 2 of the dreamos restructuring.
It updates import statements in Python files to use the new package structure.
"""

import os
import re
import json
import logging
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configuration
ROOT_DIR = Path("dreamos")
MOVE_MAP_FILE = ROOT_DIR / "file_move_map.json"
BACKUP_DIR = Path("backups") / f"dreamos_restructure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
DRY_RUN = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"import_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_backup():
    """Create a backup of the dreamos directory."""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True)
    
    # Copy files to backup
    for file in ROOT_DIR.rglob("*.py"):
        rel_path = file.relative_to(ROOT_DIR)
        backup_file = BACKUP_DIR / rel_path
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        backup_file.write_text(file.read_text())

def load_move_map() -> Dict[str, str]:
    """Load the move map from JSON file."""
    try:
        with open(MOVE_MAP_FILE, 'r') as f:
            move_map = json.load(f)
        logger.info(f"Loaded move map with {len(move_map)} entries")
        return move_map
    except Exception as e:
        logger.error(f"Failed to load move map: {e}")
        return {}

def parse_imports(file_path: Path) -> Tuple[List[str], List[str], List[str]]:
    """Parse imports from a Python file."""
    imports = []
    from_imports = []
    relative_imports = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all import statements
        import_pattern = r'^(?:from\s+([\w.]+)\s+import\s+.*|import\s+([\w.]+).*)$'
        for line in content.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                module = match.group(1) or match.group(2)
                if module.startswith('.'):
                    relative_imports.append((line.strip(), module))
                else:
                    imports.append((line.strip(), module))
                    
        return imports, from_imports, relative_imports
    except Exception as e:
        logger.error(f"Failed to parse imports in {file_path}: {e}")
        return [], [], []

def update_imports(file_path: Path, move_map: Dict[str, str]) -> bool:
    """Update imports in a Python file based on the move map."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        new_content = content
        
        # Update standard imports
        for old_path, new_path in move_map.items():
            old_module = old_path.replace('\\', '.').replace('/', '.')
            new_module = new_path.replace('\\', '.').replace('/', '.')
            
            # Handle both import styles
            patterns = [
                (f'from {old_module} import', f'from {new_module} import'),
                (f'import {old_module}', f'import {new_module}'),
                (f'from {old_module}.', f'from {new_module}.'),
                (f'import {old_module}.', f'import {new_module}.')
            ]
            
            for old_pattern, new_pattern in patterns:
                if old_pattern in new_content:
                    new_content = new_content.replace(old_pattern, new_pattern)
                    modified = True
                    
        # Update relative imports
        if modified:
            # Format the file
            try:
                subprocess.run(['black', str(file_path)], check=True)
                subprocess.run(['isort', str(file_path)], check=True)
            except Exception as e:
                logger.error(f"Failed to format {file_path}: {e}")
                
        return modified
    except Exception as e:
        logger.error(f"Failed to update imports in {file_path}: {e}")
        return False

def format_file(file_path: Path) -> None:
    """Format a Python file using black and isort."""
    if DRY_RUN:
        logger.info(f"Would format {file_path}")
        return
    
    try:
        # Run isort
        subprocess.run(["isort", str(file_path)], check=True)
        # Run black
        subprocess.run(["black", str(file_path)], check=True)
        logger.info(f"Formatted {file_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to format {file_path}: {e}")

def run_tests() -> bool:
    """Run tests to verify changes."""
    if DRY_RUN:
        logger.info("Would run tests")
        return True
    
    try:
        result = subprocess.run(["pytest", "tests/", "--maxfail=10", "-v"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("All tests passed")
            return True
        else:
            logger.error(f"Tests failed:\n{result.stdout}\n{result.stderr}")
            return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run tests: {e}")
        return False

def main():
    """Main function to execute the import updates."""
    logger.info("Starting import updates")
    
    # Create backup
    create_backup()
    
    # Load move map
    move_map = load_move_map()
    if not move_map:
        logger.error("Failed to load move map. Aborting.")
        return
    
    # Find all Python files
    python_files = []
    for root, _, files in os.walk(ROOT_DIR):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(python_files)} Python files")
    
    # Update imports
    modified_files = 0
    for file_path in python_files:
        if update_imports(file_path, move_map):
            modified_files += 1
            logger.info(f"Modified {file_path}")
    
    logger.info(f"Modified {modified_files} files")
    
    # Run tests
    if not run_tests():
        logger.error("Tests failed after import updates")
        logger.info("Restoring from backup...")
        try:
            shutil.rmtree(ROOT_DIR)
            shutil.copytree(BACKUP_DIR, ROOT_DIR)
            logger.info("Restored from backup successfully")
        except Exception as e:
            logger.error(f"Failed to restore from backup: {e}")
        return
    
    logger.info("Import updates completed successfully")

if __name__ == "__main__":
    main() 