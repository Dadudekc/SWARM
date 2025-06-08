"""
Dream.OS Launcher

Main script to initialize and start all Dream.OS components.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from PyQt5.QtWidgets import QApplication

from dreamos.core.agent_control.agent_operations import AgentOperations
from dreamos.core.agent_control.agent_restarter import AgentRestarter
from dreamos.core.agent_control.agent_onboarder import AgentOnboarder
from dreamos.core.agent_control.high_priority_dispatcher import HighPriorityDispatcher
from dreamos.core.agent_control.agent_cellphone import AgentCellphone
from dreamos.core.utils.message_processor import MessageProcessor
from dreamos.core.utils.agent_status import AgentStatus
from dreamos.core.ui.agent_dashboard import AgentDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dreamos.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class DreamOSLauncher:
    """Launches and manages Dream.OS components."""
    
    def __init__(self):
        """Initialize the launcher."""
        self.config_dir = "config"
        self.status_file = os.path.join(self.config_dir, "agent_status.json")
        self.onboarding_config = os.path.join(self.config_dir, "onboarding_config.json")
        
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        # Initialize status file if needed
        self._init_status_file()
        
    def _init_status_file(self):
        """Initialize agent status file if it doesn't exist."""
        if not os.path.exists(self.status_file):
            initial_status = {
                "agent-1": {
                    "last_heartbeat": datetime.now().isoformat(),
                    "status": "initializing",
                    "current_task": "BOOT-SEQUENCE"
                }
            }
            with open(self.status_file, 'w') as f:
                json.dump(initial_status, f, indent=2)
                
    async def start(self):
        """Start all Dream.OS components."""
        try:
            # Initialize core components
            message_processor = MessageProcessor()
            agent_status = AgentStatus(self.status_file)
            agent_ops = AgentOperations(message_processor, agent_status)
            cell_phone = AgentCellphone()
            
            # Initialize control components
            dispatcher = HighPriorityDispatcher(message_processor, agent_ops)
            restarter = AgentRestarter(agent_ops, cell_phone, self.status_file)
            onboarder = AgentOnboarder(agent_ops, cell_phone, self.onboarding_config)
            
            # Start Qt application
            app = QApplication(sys.argv)
            
            # Create and show dashboard
            dashboard = AgentDashboard(agent_ops, restarter, onboarder)
            dashboard.show()
            
            # Start background tasks
            asyncio.create_task(restarter.start_monitoring())
            
            # Start Qt event loop
            return app.exec_()
            
        except Exception as e:
            logger.error(f"Error starting Dream.OS: {e}")
            return 1
            
def main():
    """Main entry point."""
    try:
        launcher = DreamOSLauncher()
        return asyncio.run(launcher.start())
    except KeyboardInterrupt:
        logger.info("Dream.OS shutdown requested")
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
        
if __name__ == "__main__":
    sys.exit(main()) 