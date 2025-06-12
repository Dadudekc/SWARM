#!/usr/bin/env python3
"""
Agent Tools Restructuring Script - Phase 1

This script handles the first phase of restructuring the agent_tools directory:
1. Creates new directory structure
2. Generates move map
3. Copies files to new locations
4. Cleans up empty directories and __pycache__
"""

import json
import os
import shutil
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configuration
ROOT_DIR = Path("agent_tools")
DRY_RUN = False  # Set to True to preview changes
MOVE_MAP_FILE = ROOT_DIR / "file_move_map.json"
BACKUP_DIR = Path("backups") / f"agent_tools_restructure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"restructure_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# New directory structure
NEW_STRUCTURE = {
    "core": {
        "autonomy": {},
        "bridge": {},
        "config": {},
        "security": {},
        "utils": {}
    },
    "config": {
        "schemas": {},
        "templates": {}
    },
    "swarm": {
        "analyzers": {},
        "browser": {},
        "metrics": {},
        "models": {},
        "reporters": {},
        "scanners": {},
        "utils": {}
    },
    "utils": {
        "retry": {},
        "mailbox": {}
    },
    "tests": {
        "unit": {},
        "integration": {}
    },
    "docs": {
        "guides": {},
        "api": {}
    },
    "scripts": {}
}

# File move mapping
FILE_MOVES = {
    # Core moves
    "autonomy/task_completion.py": "core/autonomy/task_completion.py",
    "autonomy/loop.py": "core/autonomy/loop.py",
    "bridge/cursor_chatgpt_bridge.py": "core/bridge/cursor_chatgpt_bridge.py",
    "config/schema.py": "core/config/schema.py",
    "config/config_loader.py": "core/config/config_loader.py",
    "security/security_overlay_generator.py": "core/security/security_overlay_generator.py",
    "utils/retry_utils.py": "core/utils/retry_utils.py",
    "utils/init_mailbox.py": "core/utils/init_mailbox.py",
    
    # Config moves
    "config/schema.yaml": "config/schemas/schema.yaml",
    "config/config.yaml": "config/schemas/config.yaml",
    "security/template/": "config/templates/security/",
    
    # Swarm moves
    "swarm_tools/analyzers/": "swarm/analyzers/",
    "swarm_tools/browser/": "swarm/browser/",
    "swarm_tools/metrics/": "swarm/metrics/",
    "swarm_tools/models/": "swarm/models/",
    "swarm_tools/reporters/": "swarm/reporters/",
    "swarm_tools/scanners/": "swarm/scanners/",
    "swarm_tools/utils/": "swarm/utils/",
    
    # Utils moves
    "utils/retry_utils.py": "utils/retry/retry_utils.py",
    "utils/init_mailbox.py": "utils/mailbox/init_mailbox.py",
    
    # Test moves
    "tests/unit/": "tests/unit/",
    "tests/integration/": "tests/integration/"
}

def create_backup() -> bool:
    """Create a backup of the agent_tools directory."""
    try:
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(ROOT_DIR, BACKUP_DIR)
        logger.info(f"Created backup at {BACKUP_DIR}")
        return True
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        return False

def create_directories():
    """Create the new directory structure."""
    for dir_path in NEW_STRUCTURE.keys():
        full_path = ROOT_DIR / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True)
            logger.info(f"Created directory: {full_path}")

def find_pycache_dirs():
    """Find all __pycache__ directories."""
    pycache_dirs = []
    for root, dirs, _ in os.walk(ROOT_DIR):
        if "__pycache__" in dirs:
            pycache_dirs.append(os.path.join(root, "__pycache__"))
    return pycache_dirs

def find_empty_dirs():
    """Find all empty directories."""
    empty_dirs = []
    for root, dirs, files in os.walk(ROOT_DIR, topdown=False):
        if not dirs and not files and root != str(ROOT_DIR):
            empty_dirs.append(root)
    return empty_dirs

def move_files():
    """Move files according to the move map."""
    move_map = {}
    for src, dst in FILE_MOVES.items():
        src_path = ROOT_DIR / src
        dst_path = ROOT_DIR / dst
        
        if src_path.exists():
            # Create destination directory if it doesn't exist
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not DRY_RUN:
                try:
                    if src_path.is_dir():
                        if dst_path.exists():
                            shutil.rmtree(dst_path)
                        shutil.move(str(src_path), str(dst_path))
                    else:
                        shutil.move(str(src_path), str(dst_path))
                    logger.info(f"Moved {src} to {dst}")
                    move_map[str(src_path)] = str(dst_path)
                except Exception as e:
                    logger.error(f"Failed to move {src} to {dst}: {e}")
            else:
                logger.info(f"Would move {src} to {dst}")
                move_map[str(src_path)] = str(dst_path)
    
    return move_map

def cleanup_old_dirs():
    """Clean up old directories after moves."""
    old_dirs = [
        "autonomy",
        "bridge",
        "config",
        "security",
        "swarm_tools",
        "utils"
    ]
    
    for dir_name in old_dirs:
        dir_path = ROOT_DIR / dir_name
        if dir_path.exists():
            try:
                if not DRY_RUN:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed old directory: {dir_path}")
                else:
                    logger.info(f"Would remove old directory: {dir_path}")
            except Exception as e:
                logger.error(f"Failed to remove {dir_path}: {e}")

def main():
    """Main function to execute the restructuring."""
    logger.info("Starting restructuring process")
    
    # Create backup
    if not create_backup():
        logger.error("Failed to create backup. Aborting.")
        return
    
    # Create new directory structure
    create_directories()
    
    # Move files
    move_map = move_files()
    
    # Save move map
    if not DRY_RUN:
        with open(MOVE_MAP_FILE, 'w') as f:
            json.dump(move_map, f, indent=2)
        logger.info(f"Saved move map to {MOVE_MAP_FILE}")
    
    # Find and report __pycache__ directories
    pycache_dirs = find_pycache_dirs()
    if pycache_dirs:
        logger.info(f"Found {len(pycache_dirs)} __pycache__ directories:")
        for d in pycache_dirs:
            logger.info(f"  {d}")
    
    # Find and report empty directories
    empty_dirs = find_empty_dirs()
    if empty_dirs:
        logger.info(f"Found {len(empty_dirs)} empty directories:")
        for d in empty_dirs:
            logger.info(f"  {d}")
    
    # Clean up old directories
    cleanup_old_dirs()
    
    logger.info("Restructuring completed successfully")

if __name__ == "__main__":
    main() 