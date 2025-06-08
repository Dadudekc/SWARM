"""
Bridge Configuration Migration Script
-----------------------------------
Helps users migrate from the old bridge config to the new unified config manager.
"""

import os
import sys
import yaml
import json
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dreamos.core.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)

def load_old_config(config_path: str) -> dict:
    """Load configuration from old YAML file.
    
    Args:
        config_path: Path to old YAML config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Failed to load old config: {e}")
        return {}

def migrate_config(old_config_path: str) -> None:
    """Migrate configuration from old format to new.
    
    Args:
        old_config_path: Path to old YAML config file
    """
    # Load old config
    old_config = load_old_config(old_config_path)
    if not old_config:
        logger.error("No configuration found to migrate")
        return
        
    # Initialize new config manager
    config_manager = ConfigManager()
    
    # Map old config to new format
    bridge_config = {
        'headless': old_config.get('headless', False),
        'window_size': old_config.get('window_size', (1920, 1080)),
        'page_load_wait': old_config.get('page_load_wait', 10),
        'element_wait': old_config.get('element_wait', 5),
        'response_wait': old_config.get('response_wait', 5),
        'paste_delay': old_config.get('paste_delay', 0.5),
        'health_check_interval': old_config.get('health_check_interval', 30),
        'user_data_dir': old_config.get('user_data_dir'),
        'cursor_window_title': old_config.get('cursor_window_title', "Cursor – agent")
    }
    
    # Update new config
    config_manager.set_bridge_config(bridge_config)
    
    # Save old config as backup
    backup_path = Path(old_config_path).with_suffix('.yaml.bak')
    try:
        with open(backup_path, 'w') as f:
            yaml.dump(old_config, f)
        logger.info(f"Backed up old config to {backup_path}")
    except Exception as e:
        logger.error(f"Failed to backup old config: {e}")
    
    logger.info("Configuration migration completed successfully")
    logger.info(f"New config location: {config_manager.config_file}")

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) != 2:
        print("Usage: python migrate_bridge_config.py <old_config_path>")
        sys.exit(1)
        
    old_config_path = sys.argv[1]
    if not os.path.exists(old_config_path):
        logger.error(f"Config file not found: {old_config_path}")
        sys.exit(1)
        
    migrate_config(old_config_path)

if __name__ == '__main__':
    main() 
