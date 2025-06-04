"""
System Initialization Module

Handles core system initialization and communication channel setup.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional

from .message_processor import MessageProcessor
from .coordinate_manager import CoordinateManager
from .messaging.cell_phone import CellPhone
from .agent_logger import AgentLogger

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
            
            # Initialize message processor
            self.message_processor = MessageProcessor()
            
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
            results = self.message_processor.send_to_all_agents(
                "Communication channel test. Please respond if you receive this message.",
                mode="TEST"
            )
            
            # Check results
            successful = sum(1 for success in results.values() if success)
            logger.info(f"Established communication with {successful}/{len(agents)} agents")
            
            return successful > 0
            
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
            self.message_processor.send_to_all_agents(
                "Beginning domain monitoring. Please report any significant events.",
                mode="MONITOR"
            )
            
            # Start continuous monitoring loop
            while True:
                # Process any queued messages
                self.message_processor.process_queue()
                
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
                "message_processor": bool(self.message_processor),
                "coordinate_manager": bool(self.coordinate_manager),
                "cell_phone": bool(self.cell_phone),
                "agent_logger": bool(self.agent_logger)
            }
            
            logger.info("System status report generated")
            return status
            
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return {}

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