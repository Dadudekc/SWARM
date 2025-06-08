"""
Response Loop Daemon
------------------
Monitors agent responses and generates new prompts for the ChatGPT bridge.
Implements the full Cursor-ChatGPT communication loop.
"""

import json
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import jinja2
import time

from dreamos.core.autonomy.base.response_loop_daemon import BaseResponseLoopDaemon
from dreamos.core.autonomy.memory.response_memory_tracker import ResponseMemoryTracker
from dreamos.core.autonomy.processors.factory import ResponseProcessorFactory
from dreamos.core.autonomy.processors.mode import ProcessorMode
from dreamos.core.autonomy.utils.response_utils import extract_agent_id_from_file
from .monitoring import BridgeMonitor
from .discord_hook import DiscordHook, EventType
from .chatgpt_bridge_loop import ChatGPTBridgeLoop

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResponseLoopDaemon(BaseResponseLoopDaemon):
    """Response loop daemon implementation for Cursor-ChatGPT communication."""
    
    def __init__(self, config_path: str, discord_token: Optional[str] = None):
        """Initialize the response loop daemon.
        
        Args:
            config_path: Path to configuration file
            discord_token: Optional Discord token for notifications
        """
        super().__init__(config_path, discord_token)
        
        # Set up paths
        self.agent_mailbox = Path(self.config["paths"]["agent_mailbox"])
        self.archive_dir = Path(self.config["paths"]["archive"])
        self.failed_dir = Path(self.config["paths"]["failed"])
        self.validated_dir = Path(self.config["paths"]["validated"])
        
        # Initialize components
        self.memory_tracker = ResponseMemoryTracker(
            str(Path(self.config["paths"]["runtime"]) / "memory" / f"response_log_{self.agent_id}.json")
        )
        self.monitor = BridgeMonitor()
        self.discord = DiscordHook()
        
        # Initialize ChatGPT bridge
        self.bridge = ChatGPTBridgeLoop(self.config["chatgpt"]["config_path"])
        
        # Set up file system observer
        self.observer = Observer()
        self.observer.schedule(
            AgentMailboxHandler(self),
            str(self.agent_mailbox),
            recursive=False
        )
        self.observer.start()
        
        # Initialize Jinja2 environment for templates
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader('bridge/prompt_templates'),
            autoescape=True
        )
    
    async def start(self):
        """Start the response loop daemon."""
        await super().start()
        self.bridge.run()  # Start in a separate thread
        logger.info("Response loop daemon started")
    
    async def stop(self):
        """Stop the response loop daemon."""
        self.bridge.driver.quit()  # Stop the browser
        await super().stop()
        logger.info("Response loop daemon stopped")
    
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
    
    async def _process_response_file(self, file_path: Path):
        """Process a response file.
        
        Args:
            file_path: Path to response file
        """
        try:
            # Load response
            with open(file_path, 'r') as f:
                response = json.load(f)
            
            # Extract agent ID
            agent_id = extract_agent_id_from_file(file_path)
            if not agent_id:
                logger.error(f"Could not extract agent ID from {file_path}")
                return
            
            # Generate prompt
            prompt = self._generate_prompt(response, agent_id)
            
            # Send to ChatGPT
            success = await self._send_to_chatgpt(prompt, agent_id)
            if not success:
                logger.error(f"Failed to send prompt to ChatGPT for agent {agent_id}")
                return
            
            # Move to archive
            archive_path = self.archive_dir / file_path.name
            file_path.rename(archive_path)
            
            # Update metrics
            self.monitor.update_metrics(
                agent_id=agent_id,
                prompt_type=prompt["metadata"]["context"]
            )
            
            # Send Discord notification
            self.discord.send_prompt_status(
                agent_id=agent_id,
                prompt_type=prompt["metadata"]["context"],
                success=True
            )
            
        except Exception as e:
            logger.error(f"Error processing response file {file_path}: {e}")
            # Move to failed directory
            failed_path = self.failed_dir / file_path.name
            file_path.rename(failed_path)
            
            # Send Discord notification
            self.discord.send_prompt_status(
                agent_id=agent_id,
                prompt_type="error",
                success=False,
                error=str(e)
            )
    
    def _generate_prompt(self, response: Dict[str, Any], agent_id: str) -> Dict[str, Any]:
        """Generate a prompt from a response.
        
        Args:
            response: Response data
            agent_id: Agent ID
            
        Returns:
            Generated prompt
        """
        response_type = response.get("type", "general")
        template = self._get_template(response_type)
        
        if template:
            # Render template with response data
            prompt_text = template.render(
                response=response,
                agent_id=agent_id,
                timestamp=datetime.now().isoformat()
            )
        else:
            # Fallback to default prompt generation
            prompt_text = f"Please analyze the following response from agent {agent_id}:\n\n{json.dumps(response, indent=2)}\n\nWhat should be the next step?"
        
        return {
            "prompt": prompt_text,
            "timestamp": datetime.now().isoformat(),
            "priority": response.get("priority", 1),
            "metadata": {
                "source": "response_loop",
                "context": response_type,
                "original_response": response
            }
        }
    
    def _get_template(self, response_type: str) -> Optional[jinja2.Template]:
        """Get the appropriate template for the response type.
        
        Args:
            response_type: Type of response
            
        Returns:
            Jinja2 template or None if not found
        """
        try:
            template_name = f"{response_type}.j2"
            return self.template_env.get_template(template_name)
        except Exception as e:
            logger.warning(f"No template found for {response_type}, using default: {e}")
            return None
    
    async def _send_to_chatgpt(self, prompt: Dict[str, Any], agent_id: str) -> bool:
        """Send a prompt to ChatGPT.
        
        Args:
            prompt: Prompt data
            agent_id: Agent ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Write prompt to bridge outbox
            outbox_path = Path(self.config["paths"]["bridge_outbox"]) / f"agent-{agent_id}.json"
            with open(outbox_path, 'w') as f:
                json.dump(prompt, f, indent=2)
            
            # Wait for response
            validated_path = self.validated_dir / f"agent-{agent_id}.json"
            start_time = time.time()
            while time.time() - start_time < self.config["chatgpt"]["response_wait"]:
                if validated_path.exists():
                    # Read and validate response
                    with open(validated_path) as f:
                        response = json.load(f)
                    if self._validate_response(response):
                        return True
                await asyncio.sleep(1)
            
            logger.error(f"Timeout waiting for ChatGPT response for agent {agent_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending prompt to ChatGPT: {e}")
            return False
    
    def _validate_response(self, response: Dict[str, Any]) -> bool:
        """Validate a ChatGPT response.
        
        Args:
            response: Response to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not response or "content" not in response:
            logger.warning(f"Invalid response format: {response}")
            return False
            
        if "error" in response:
            logger.warning(f"Response contains error: {response['error']}")
            return False
            
        return True

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
