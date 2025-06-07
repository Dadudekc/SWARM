"""
Bridge Response Loop Daemon
-------------------------
Monitors agent mailbox for responses and generates new prompts for the ChatGPT bridge.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jinja2

from dreamos.core.autonomy.base.response_loop_daemon import BaseResponseLoopDaemon
from dreamos.core.autonomy.memory.response_memory_tracker import ResponseMemoryTracker
from dreamos.core.autonomy.processor_factory import ResponseProcessorFactory, ProcessorMode
from dreamos.core.autonomy.utils.response_utils import extract_agent_id_from_file
from .monitoring import BridgeMonitor
from .discord_hook import DiscordHook, EventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BridgeResponseLoopDaemon(BaseResponseLoopDaemon):
    """Bridge response loop daemon implementation."""
    
    def __init__(self, config_path: str, discord_token: Optional[str] = None):
        """Initialize the bridge response loop daemon.
        
        Args:
            config_path: Path to configuration file
            discord_token: Optional Discord token for notifications
        """
        super().__init__(config_path, discord_token)
        
        # Set up paths
        self.agent_mailbox = Path(self.config["paths"]["agent_mailbox"])
        self.archive_dir = Path(self.config["paths"]["archive"])
        self.failed_dir = Path(self.config["paths"]["failed"])
        
        # Initialize memory tracker
        memory_path = Path(self.config["paths"]["runtime"]) / "memory" / f"response_log_{self.agent_id}.json"
        self.memory_tracker = ResponseMemoryTracker(str(memory_path))
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            AgentMailboxHandler(self),
            str(self.agent_mailbox),
            recursive=False
        )
        self.observer.start()
    
    def _create_response_processor(self) -> ResponseProcessor:
        """Create the response processor implementation.
        
        Returns:
            ResponseProcessor instance
        """
        return ResponseProcessorFactory.create_processor(ProcessorMode.BRIDGE)
    
    def _get_response_files(self) -> List[Path]:
        """Get all response files to process.
        
        Returns:
            List of response file paths
        """
        return list(self.agent_mailbox.glob("*.json"))
    
    async def _resume_agent_impl(self, agent_id: str) -> bool:
        """Implementation-specific agent resume logic.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if agent is in failed state
            if self.agent_state.get_agent_state(agent_id).get("status") == "failed":
                # Move failed files to archive
                failed_files = list(self.failed_dir.glob(f"{agent_id}_*.json"))
                for file in failed_files:
                    archive_path = self.archive_dir / file.name
                    file.rename(archive_path)
            
            # Reset agent state
            self.agent_state.update_agent_state(agent_id, "idle")
            return True
            
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
            return False

class AgentMailboxHandler(FileSystemEventHandler):
    """Handles file creation events in agent mailbox."""
    
    def __init__(self, daemon: BridgeResponseLoopDaemon):
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