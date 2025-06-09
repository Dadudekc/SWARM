"""
System Initialization Module

Handles system-wide initialization and configuration.
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional
import json

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from .config import ConfigManager
from .logging.log_config import setup_logging
from .messaging.message_processor import MessageProcessor
from .shared.coordinate_manager import CoordinateManager
from .messaging.cell_phone import CellPhone
from .logging.agent_logger import AgentLogger
from .agent_control.ui_automation import UIAutomation
from .agent_control.agent_operations import AgentOperations
from tests.utils.test_utils import TEST_RUNTIME_DIR

logger = logging.getLogger('system_init')

class SystemInitializer:
    """Handles system initialization and communication setup."""
    
    def __init__(self, agent_id: str = "system"):
        """Initialize the system initializer.
        
        Args:
            agent_id: The ID of the agent to initialize for (default: "system")
        """
        self.agent_id = agent_id
        self.message_processor = None
        self.coordinate_manager = None
        self.cell_phone = None
        self.agent_logger = None
        
    def initialize_core_systems(self) -> bool:
        """Initialize all core systems.
        
        Returns:
            True if initialization was successful
        """
        try:
            logger.info("Initializing core systems...")
            
            # Initialize coordinate manager
            self.coordinate_manager = CoordinateManager()
            if not self.coordinate_manager.coordinates:
                logger.error("Failed to load agent coordinates")
                return False
                
            # Initialize cell phone (message queue)
            self.cell_phone = CellPhone()
            
            # Initialize message processor with runtime directory
            self.message_processor = MessageProcessor(runtime_dir=str(TEST_RUNTIME_DIR))
            
            # Initialize agent logger with agent ID
            self.agent_logger = AgentLogger(self.agent_id)
            
            logger.info("Core systems initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing core systems: {e}")
            return False
            
    def establish_communication_channels(self) -> bool:
        """Establish communication channels with all agents.
        
        Returns:
            True if channels were established successfully
        """
        try:
            logger.info("Establishing communication channels...")
            
            # Get list of available agents
            agents = self.coordinate_manager.list_agents()
            if not agents:
                logger.error("No agents available for communication")
                return False
                
            # Send test message to each agent
            for agent_id in agents:
                self.cell_phone.send_message(
                    to_agent=agent_id,
                    content="Communication channel test. Please respond if you receive this message.",
                    mode="TEST"
                )
            
            logger.info(f"Established communication with {len(agents)} agents")
            return True
            
        except Exception as e:
            logger.error(f"Error establishing communication channels: {e}")
            return False
            
    def begin_monitoring(self) -> None:
        """Begin monitoring assigned domains."""
        try:
            logger.info("Starting domain monitoring...")
            
            # Get list of agents
            agents = self.coordinate_manager.list_agents()
            
            # Send monitoring start message
            for agent_id in agents:
                self.cell_phone.send_message(
                    to_agent=agent_id,
                    content="Beginning domain monitoring. Please report any significant events.",
                    mode="MONITOR"
                )
            
            # Start continuous monitoring loop
            while True:
                # Check agent status
                for agent_id in agents:
                    status = self.cell_phone.get_agent_status(agent_id)
                    if status:
                        logger.info(f"Agent {agent_id} status: {status}")
                
                # Sleep to prevent CPU overuse
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            
    def report_status(self) -> Dict[str, any]:
        """Report current system status.
        
        Returns:
            Dictionary containing system status information
        """
        try:
            status = {
                "timestamp": time.time(),
                "agents": self.coordinate_manager.list_agents(),
                "queue_size": self.cell_phone.queue.size() if self.cell_phone else 0,
                "coordinate_manager": bool(self.coordinate_manager),
                "cell_phone": bool(self.cell_phone),
                "agent_logger": bool(self.agent_logger)
            }
            
            logger.info("System status report generated")
            return status
            
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return {}

# Create singleton instance
_system_initializer = SystemInitializer()

def initialize_core_systems() -> bool:
    """Initialize all core systems.
    
    Returns:
        True if initialization was successful
    """
    return _system_initializer.initialize_core_systems()

__all__ = [
    'SystemInitializer',
    'initialize_core_systems',
    'establish_communication_channels',
    'begin_monitoring',
    'report_status'
]

def main():
    """Main entry point for system initialization."""
    initializer = SystemInitializer()
    
    # Initialize core systems
    if not initializer.initialize_core_systems():
        logger.error("Failed to initialize core systems")
        return
        
    # Establish communication channels
    if not initializer.establish_communication_channels():
        logger.error("Failed to establish communication channels")
        return
        
    # Report initial status
    status = initializer.report_status()
    logger.info("Initial system status:")
    for key, value in status.items():
        logger.info(f"{key}: {value}")
        
    # Begin monitoring
    initializer.begin_monitoring()

if __name__ == "__main__":
    main() 
