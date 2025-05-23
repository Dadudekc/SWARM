"""
Dream.OS Core Module

Core functionality for the Dream.OS system.
"""

import logging
from pathlib import Path
from typing import Optional

from .system_init import SystemInitializer
from .message_processor import MessageProcessor
from .coordinate_manager import CoordinateManager
from .cell_phone import CellPhone
from .agent_logger import AgentLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('dreamos.core')

def initialize_system(agent_id: str = "system") -> Optional[SystemInitializer]:
    """Initialize the Dream.OS system.
    
    Args:
        agent_id: The ID of the agent to initialize for
        
    Returns:
        SystemInitializer instance if successful, None otherwise
    """
    try:
        # Create runtime directories if they don't exist
        runtime_dir = Path("runtime")
        runtime_dir.mkdir(exist_ok=True)
        
        config_dir = runtime_dir / "config"
        config_dir.mkdir(exist_ok=True)
        
        agent_memory_dir = runtime_dir / "agent_memory"
        agent_memory_dir.mkdir(exist_ok=True)
        
        # Initialize system
        initializer = SystemInitializer(agent_id)
        
        # Initialize core systems
        if not initializer.initialize_core_systems():
            logger.error("Failed to initialize core systems")
            return None
            
        # Establish communication channels
        if not initializer.establish_communication_channels():
            logger.error("Failed to establish communication channels")
            return None
            
        logger.info(f"Dream.OS system initialized for agent {agent_id}")
        return initializer
        
    except Exception as e:
        logger.error(f"Error initializing Dream.OS system: {e}")
        return None

__all__ = [
    'SystemInitializer',
    'MessageProcessor',
    'CoordinateManager',
    'CellPhone',
    'AgentLogger',
    'initialize_system'
]
