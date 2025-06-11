"""
Response Loop Daemon
-----------------
Monitors agent responses and generates new prompts for the ChatGPT bridge.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from dreamos.core.bridge.base import BridgeHandler
from dreamos.core.bridge.monitoring import BridgeMonitor
from dreamos.core.shared.processors import ProcessorMode
from dreamos.core.utils.core_utils import (
    get_timestamp,
    format_timestamp,
    generate_id
)
from dreamos.core.utils.json_utils import load_json
from dreamos.core.utils.logging_utils import get_logger
from dreamos.core.autonomy.base.response_loop_daemon import BaseResponseLoopDaemon
from dreamos.core.autonomy.memory.response_memory_tracker import ResponseMemoryTracker
from dreamos.core.autonomy.processors.factory import ProcessorFactory
from dreamos.core.autonomy.processors.response import ResponseProcessor
from dreamos.core.autonomy.utils.response_utils import extract_agent_id_from_file
from dreamos.core.utils.core_utils import (
    format_duration,
    is_valid_uuid
)
from dreamos.core.utils import safe_move

# Configure logging
logger = logging.getLogger(__name__)

class ResponseLoopDaemon(BaseResponseLoopDaemon):
    """Monitors agent responses and generates new prompts for the ChatGPT bridge."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, discord_token: Optional[str] = None):
        """Initialize the response loop daemon.
        
        Args:
            config: Optional configuration dictionary
            discord_token: Optional Discord token for notifications
        """
        super().__init__(config)
        
        # Initialize components
        self.bridge = BridgeHandler(config)
        
        # Set up paths
        self.runtime_dir = Path(self.config.get("paths", {}).get("runtime", "data/runtime"))
        self.agent_mailbox = Path(self.config.get("paths", {}).get("agent_mailbox", "data/mailbox"))
        self.archive_dir = Path(self.config.get("paths", {}).get("archive", "data/archive"))
        self.failed_dir = Path(self.config.get("paths", {}).get("failed", "data/failed"))
        
        # Create directories
        for directory in [self.runtime_dir, self.agent_mailbox, self.archive_dir, self.failed_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize memory tracker
        memory_path = self.runtime_dir / "memory" / f"response_log_{self.agent_id}.json"
        self.memory_tracker = ResponseMemoryTracker(str(memory_path))
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            AgentMailboxHandler(self),
            str(self.agent_mailbox),
            recursive=False
        )
        
        # Initialize monitoring
        self.monitor = BridgeMonitor()
        self.discord = DiscordHook(discord_token)
        
        # Load state
        self.state_file = self.runtime_dir / "response_loop_state.json"
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """Load daemon state from file.
        
        Returns:
            Dict containing daemon state
        """
        try:
            if self.state_file.exists():
                return load_json(str(self.state_file))
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}
    
    def _save_state(self):
        """Save daemon state to file."""
        try:
            save_json(str(self.state_file), self.state)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _create_response_processor(self) -> ResponseProcessor:
        """Create the response processor implementation.
        
        Returns:
            ResponseProcessor instance
        """
        factory = ProcessorFactory()
        return factory.create('response', self.config)
    
    def _get_response_files(self) -> List[Path]:
        """Get all response files to process.
        
        Returns:
            List of response file paths
        """
        return list(self.agent_mailbox.glob("*.json"))
    
    async def _process_response_file(self, file_path: Path) -> bool:
        """Process a response file.
        
        Args:
            file_path: Path to response file
            
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            # Extract agent ID from filename
            agent_id = extract_agent_id_from_file(file_path)
            if not agent_id:
                logger.error(f"Could not extract agent ID from {file_path}")
                return False
            
            # Read response data
            with open(file_path, 'r') as f:
                response_data = json.load(f)
            
            # Process response
            success, error = await self.processor.process_response(response_data, agent_id)
            
            if success:
                # Archive successful response
                archive_path = self.archive_dir / file_path.name
                if not safe_move(str(file_path), str(archive_path)):
                    logger.error(f"Failed to archive response file {file_path}")
                    return False
                
                # Update metrics
                self.monitor.update_metrics(
                    agent_id=agent_id,
                    response_type=response_data.get("type", "unknown")
                )
                
                # Send Discord notification
                await self.discord.send_event(
                    EventType.SUCCESS,
                    f"Processed response from agent {agent_id}",
                    {"file": str(file_path)}
                )
                
                return True
            else:
                # Move failed response to failed directory
                failed_path = self.failed_dir / file_path.name
                if not safe_move(str(file_path), str(failed_path)):
                    logger.error(f"Failed to move failed response {file_path}")
                    return False
                
                # Update agent state
                self.agent_state.update_agent_state(agent_id, "failed")
                
                # Send Discord notification
                await self.discord.send_event(
                    EventType.ERROR,
                    f"Failed to process response from agent {agent_id}",
                    {"error": error, "file": str(file_path)}
                )
                
                return False
                
        except Exception as e:
            logger.error(f"Error processing response file {file_path}: {e}")
            return False
    
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
                    if not safe_move(str(file), str(archive_path)):
                        logger.error(f"Failed to move failed file {file}")
                        return False
                
                # Update agent state
                self.agent_state.update_agent_state(agent_id, "active")
                return True
            return False
        except Exception as e:
            logger.error(f"Error resuming agent {agent_id}: {e}")
            return False
    
    async def start(self):
        """Start the response loop daemon."""
        try:
            logger.info("Starting response loop daemon...")
            
            # Start components
            await self.bridge.start()
            await self.discord.start()
            self.observer.start()
            
            # Update state
            self.state["started_at"] = datetime.now().isoformat()
            self._save_state()
            
            logger.info("Response loop daemon started")
            
        except Exception as e:
            logger.error(f"Error starting daemon: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the response loop daemon."""
        try:
            logger.info("Stopping response loop daemon...")
            
            # Stop components
            await self.bridge.stop()
            await self.discord.stop()
            self.observer.stop()
            self.observer.join()
            
            # Update state
            self.state["stopped_at"] = datetime.now().isoformat()
            self._save_state()
            
            logger.info("Response loop daemon stopped")
            
        except Exception as e:
            logger.error(f"Error stopping daemon: {e}")
    
    async def run(self):
        """Run the response loop daemon."""
        try:
            # Start daemon
            await self.start()
            
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            await self.stop()
            
        except Exception as e:
            logger.error(f"Error in daemon: {e}")
            await self.stop()
    
    @classmethod
    async def create_and_run(cls, config: Optional[Dict[str, Any]] = None, discord_token: Optional[str] = None):
        """Create and run a response loop daemon.
        
        Args:
            config: Optional configuration dictionary
            discord_token: Optional Discord token for notifications
        """
        daemon = cls(config, discord_token)
        await daemon.run()

class AgentMailboxHandler(FileSystemEventHandler):
    """Handles file creation events in agent mailbox."""
    
    def __init__(self, daemon: ResponseLoopDaemon):
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