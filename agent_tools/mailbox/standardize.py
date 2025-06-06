#!/usr/bin/env python3
"""
Standardize mailbox directory structure for agent tools.
This script ensures consistent directory structure across all agent mailboxes.
"""

import os
import shutil
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Base directory for agent tools
BASE_DIR = Path("agent_tools/mailbox")

# Standard directory structure for each agent
STANDARD_DIRS = [
    "workspace",      # For agent's working files
    "general_tools",  # For shared tools
    "cache",         # For temporary files
    "logs",          # For agent-specific logs
    "data"           # For persistent data
]

def create_standard_structure():
    """Create standardized directory structure for all agent mailboxes."""
    try:
        # Create base directory if it doesn't exist
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Get existing agent directories
        agent_dirs = [d for d in BASE_DIR.iterdir() if d.is_dir() and d.name.startswith("agent-")]
        
        for agent_dir in agent_dirs:
            logger.info(f"Standardizing structure for {agent_dir.name}")
            
            # Create standard directories
            for dir_name in STANDARD_DIRS:
                dir_path = agent_dir / dir_name
                dir_path.mkdir(exist_ok=True)
                
                # Create .gitkeep to preserve empty directories
                (dir_path / ".gitkeep").touch(exist_ok=True)
            
            # Move existing files to appropriate directories
            for item in agent_dir.iterdir():
                if item.is_file() and item.name != ".gitkeep":
                    # Move to workspace by default
                    target_dir = agent_dir / "workspace"
                    shutil.move(str(item), str(target_dir / item.name))
                    logger.info(f"Moved {item.name} to workspace")
        
        logger.info("Mailbox structure standardization complete")
        
    except Exception as e:
        logger.error(f"Error standardizing mailbox structure: {e}")
        raise

if __name__ == "__main__":
    create_standard_structure() 