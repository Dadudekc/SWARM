"""
Core Response Loop Daemon
-----------------------
Core implementation of the response loop daemon.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .base.response_loop_daemon import BaseResponseLoopDaemon, ResponseProcessor
from .handlers.bridge_outbox_handler import BridgeOutboxHandler
from .validation_engine import ValidationEngine
from .memory.response_memory_tracker import ResponseMemoryTracker
from .processors.factory import ResponseProcessorFactory
from .processors.mode import ProcessorMode

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoreResponseLoopDaemon(BaseResponseLoopDaemon):
    """Core response loop daemon implementation."""
    
    def __init__(self, config_path: str, discord_token: Optional[str] = None):
        """Initialize the core response loop daemon.
        
        Args:
            config_path: Path to configuration file
            discord_token: Optional Discord token for notifications
        """
        super().__init__(config_path, discord_token)
        
        # Initialize validation engine
        self.validation_engine = ValidationEngine()
        
        # Initialize memory tracker
        memory_path = Path(self.config["paths"]["runtime"]) / "memory" / f"response_log_{self.agent_id}.json"
        self.memory_tracker = ResponseMemoryTracker(str(memory_path))
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            BridgeOutboxHandler(self),
            self.config["paths"]["bridge_outbox"],
            recursive=False
        )
        self.observer.start()
    
    def _create_response_processor(self) -> ResponseProcessor:
        """Create the response processor implementation.
        
        Returns:
            ResponseProcessor instance
        """
        return ResponseProcessorFactory.create_processor(ProcessorMode.CORE)
    
    def _get_response_files(self) -> List[Path]:
        """Get all response files to process.
        
        Returns:
            List of response file paths
        """
        return list(self.bridge_outbox.glob("*.json"))
    
    async def _resume_agent_impl(self, agent_id: str) -> bool:
        """Implementation-specific agent resume logic.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate agent state
            if not self.validation_engine.validate_agent_state(agent_id):
                return False
            
            # Resume agent
            return await self.validation_engine.resume_agent(agent_id)
            
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
            return False

class BridgeOutboxHandler(FileSystemEventHandler):
    """Handles file creation events in bridge outbox."""
    
    def __init__(self, daemon: CoreResponseLoopDaemon):
        """Initialize the handler.
        
        Args:
            daemon: Response loop daemon instance
        """
        self.daemon = daemon
    
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File system event
        """
        if event.is_directory or not event.src_path.endswith('.json'):
            return
        
        asyncio.create_task(
            self.daemon._process_response_file(Path(event.src_path))
        ) 