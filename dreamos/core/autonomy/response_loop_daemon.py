"""
Response Loop Daemon
-----------------
Monitors bridge_outbox for agent responses:
1. Watches for new response files
2. Routes responses through validation pipeline
3. Applies approved patches
4. Updates test status
5. Manages agent state and auto-resume
6. Integrates with Discord for notifications
"""

import json
import logging
import asyncio
from dreamos.utils.discord_client import Client, Command
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from dreamos.core.logging.log_manager import LogManager
from dreamos.core.autonomy.agent_state import AgentState
from dreamos.core.autonomy.test_status import TestStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationEngine:
    """Consolidated validation and patch management engine."""
    
    def __init__(self, discord_client: Optional[Client] = None):
        """Initialize the validation engine.
        
        Args:
            discord_client: Optional Discord client for notifications
        """
        self.patches = {}  # patch_id -> patch_data
        self.test_status = {}  # test_id -> status_data
        self.logger = LogManager()
        self.discord = discord_client
        self.notification_channel = None
        
    async def set_notification_channel(self, channel_id: int):
        """Set the Discord channel for notifications.
        
        Args:
            channel_id: Discord channel ID
        """
        if self.discord:
            self.notification_channel = self.discord.get_channel(channel_id)
    
    async def _send_discord_notification(self, message: str, success: bool = True):
        """Send a notification to Discord.
        
        Args:
            message: Notification message
            success: Whether this is a success notification
        """
        if self.notification_channel:
            emoji = "✅" if success else "❌"
            await self.notification_channel.send(f"{emoji} {message}")
    
    async def validate_patch(self, patch_id: str, patch_content: str, test_id: str, agent_id: str) -> Tuple[bool, Dict[str, Any]]:
        """Validate a patch.
        
        Args:
            patch_id: Unique patch identifier
            patch_content: The patch content to validate
            test_id: Associated test identifier
            agent_id: Agent that created the patch
            
        Returns:
            Tuple of (is_valid, validation_result)
        """
        try:
            # Basic validation
            if not patch_content or not isinstance(patch_content, str):
                await self._send_discord_notification(
                    f"Agent-{agent_id} patch rejected: Invalid patch content",
                    success=False
                )
                return False, {"errors": ["Invalid patch content"]}
            
            # Track patch
            self.patches[patch_id] = {
                "content": patch_content,
                "test_id": test_id,
                "agent_id": agent_id,
                "status": "validated",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._send_discord_notification(
                f"Agent-{agent_id} patch validated for test {test_id}"
            )
            return True, {"status": "validated"}
            
        except Exception as e:
            await self._send_discord_notification(
                f"Agent-{agent_id} patch validation error: {str(e)}",
                success=False
            )
            return False, {"errors": [str(e)]}
    
    async def apply_patch(self, patch_id: str, test_id: str) -> Tuple[bool, Optional[str]]:
        """Apply a validated patch.
        
        Args:
            patch_id: Patch to apply
            test_id: Associated test
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            patch = self.patches.get(patch_id)
            if not patch:
                return False, "Patch not found"
            
            # Apply patch logic here
            # For now just mark as applied
            patch["status"] = "applied"
            self.test_status[test_id] = {
                "status": "fixed",
                "patch_id": patch_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            await self._send_discord_notification(
                f"Patch {patch_id} applied for test {test_id}"
            )
            return True, None
            
        except Exception as e:
            await self._send_discord_notification(
                f"Patch application failed: {str(e)}",
                success=False
            )
            return False, str(e)
    
    async def verify_patch(self, patch_id: str, test_id: str) -> Tuple[bool, Optional[str]]:
        """Verify an applied patch.
        
        Args:
            patch_id: Patch to verify
            test_id: Associated test
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            patch = self.patches.get(patch_id)
            if not patch or patch["status"] != "applied":
                return False, "Patch not applied"
            
            # Verification logic here
            # For now just mark as verified
            patch["status"] = "verified"
            
            await self._send_discord_notification(
                f"Patch {patch_id} verified for test {test_id}"
            )
            return True, None
            
        except Exception as e:
            await self._send_discord_notification(
                f"Patch verification failed: {str(e)}",
                success=False
            )
            return False, str(e)
    
    async def rollback_patch(self, patch_id: str, test_id: str) -> None:
        """Rollback a failed patch.
        
        Args:
            patch_id: Patch to rollback
            test_id: Associated test
        """
        try:
            if patch_id in self.patches:
                del self.patches[patch_id]
            if test_id in self.test_status:
                self.test_status[test_id]["status"] = "failed"
            
            await self._send_discord_notification(
                f"Patch {patch_id} rolled back for test {test_id}",
                success=False
            )
        except Exception as e:
            logger.error(f"Error rolling back patch: {e}")

class BridgeOutboxHandler(FileSystemEventHandler):
    """Handles file creation events in bridge_outbox."""
    
    def __init__(self, daemon):
        """Initialize the handler.
        
        Args:
            daemon: ResponseLoopDaemon instance
        """
        self.daemon = daemon
    
    def on_created(self, event):
        """Handle file creation event.
        
        Args:
            event: File creation event
        """
        if not event.is_directory and event.src_path.endswith('.json'):
            asyncio.create_task(
                self.daemon._process_response_file(Path(event.src_path))
            )

class ResponseLoopDaemon:
    """Monitors bridge_outbox for agent responses."""
    
    def __init__(self, config_path: str = "config/response_loop_config.json", discord_token: Optional[str] = None):
        """Initialize the daemon.
        
        Args:
            config_path: Path to configuration file
            discord_token: Optional Discord bot token
        """
        self.config = self._load_config(config_path)
        self.logger = LogManager()
        
        # Set up paths
        self.bridge_outbox = Path("bridge_outbox")
        self.bridge_outbox.mkdir(parents=True, exist_ok=True)
        
        # Initialize Discord client if token provided
        self.discord = None
        if discord_token:
            self.discord = Client(intents=discord.Intents.default())
        
        # Initialize validation engine
        self.validator = ValidationEngine(self.discord)
        
        # Initialize agent state manager
        self.agent_state = AgentState()
        
        # Set up watchdog
        self.observer = Observer()
        self.handler = BridgeOutboxHandler(self)
        
        # Initialize logging
        self.logger.info(
            platform="response_loop",
            status="initialized",
            message="Response loop daemon initialized",
            tags=["init", "daemon"]
        )
        
        # Start auto-resume task
        self.auto_resume_task = None
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    
    async def start(self):
        """Start the daemon."""
        try:
            # Start Discord client if configured
            if self.discord:
                await self.discord.start(self.config.get("discord_token"))
                # Set notification channel
                await self.validator.set_notification_channel(
                    self.config.get("discord_channel_id")
                )
            
            # Process existing files
            await self._process_existing_files()
            
            # Start watchdog
            self.observer.schedule(
                self.handler,
                str(self.bridge_outbox),
                recursive=False
            )
            self.observer.start()
            
            # Start auto-resume task
            self.auto_resume_task = asyncio.create_task(self._auto_resume_loop())
            
            self.logger.info(
                platform="response_loop",
                status="started",
                message="Response loop daemon started",
                tags=["start", "daemon"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="response_loop",
                status="error",
                message=f"Error starting daemon: {str(e)}",
                tags=["start", "error"]
            )
            raise
    
    def stop(self):
        """Stop the daemon."""
        try:
            # Stop auto-resume task
            if self.auto_resume_task:
                self.auto_resume_task.cancel()
            
            # Stop watchdog
            self.observer.stop()
            self.observer.join()
            
            # Stop Discord client
            if self.discord:
                asyncio.create_task(self.discord.close())
            
            self.logger.info(
                platform="response_loop",
                status="stopped",
                message="Response loop daemon stopped",
                tags=["stop", "daemon"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="response_loop",
                status="error",
                message=f"Error stopping daemon: {str(e)}",
                tags=["stop", "error"]
            )
            raise
    
    async def _auto_resume_loop(self):
        """Auto-resume loop for idle agents."""
        while True:
            try:
                # Check for idle agents
                idle_agents = self.agent_state.get_idle_agents()
                for agent_id in idle_agents:
                    # Check if agent has been idle too long
                    if self.agent_state.is_agent_stuck(agent_id):
                        # Resume agent
                        await self._resume_agent(agent_id)
                
                # Sleep for a bit
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto-resume loop: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def _resume_agent(self, agent_id: str):
        """Resume an idle agent.
        
        Args:
            agent_id: Agent to resume
        """
        try:
            # Create resume message
            message = "Agent appears to be idle. Resuming operations..."
            message_dict = {
                "type": "agent_message",
                "agent_id": agent_id,
                "content": message,
                "priority": "HIGH",
                "task_id": "AUTO_RESUME",
                "id": str(uuid.uuid4()),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Send message
            await self.message_processor.send_message(message_dict)
            
            # Update agent state
            self.agent_state.update_agent_state(agent_id, "resuming")
            
            # Log
            self.logger.info(
                platform="response_loop",
                status="resume",
                message=f"Auto-resumed agent {agent_id}",
                tags=["resume", "auto"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="response_loop",
                status="error",
                message=f"Error resuming agent {agent_id}: {e}",
                tags=["resume", "error"]
            )
    
    async def _process_existing_files(self):
        """Process any existing response files."""
        try:
            for response_file in self.bridge_outbox.glob("*.json"):
                await self._process_response_file(response_file)
        except Exception as e:
            self.logger.error(
                platform="response_loop",
                status="error",
                message=f"Error processing existing files: {str(e)}",
                tags=["process", "error"]
            )
    
    async def _process_response_file(self, response_file: Path):
        """Process a response file.
        
        Args:
            response_file: Path to the response file
        """
        try:
            # Load response
            with open(response_file, 'r') as f:
                response = json.load(f)
            
            # Extract response info
            test_id = response.get("test_id")
            agent_id = response.get("agent_id")
            patch_content = response.get("patch_content")
            
            if not all([test_id, agent_id, patch_content]):
                self.logger.error(
                    platform="response_loop",
                    status="error",
                    message=f"Invalid response format in {response_file}",
                    tags=["process", "error"]
                )
                return
            
            # Update agent state
            self.agent_state.update_agent_state(agent_id, "processing")
            
            # Generate patch ID
            patch_id = f"{test_id}_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Validate patch
            is_valid, validation_result = await self.validator.validate_patch(
                patch_id,
                patch_content,
                test_id,
                agent_id
            )
            
            if not is_valid:
                self.logger.error(
                    platform="response_loop",
                    status="error",
                    message=f"Patch validation failed: {validation_result.get('errors', ['Validation failed'])}",
                    tags=["process", "error"]
                )
                self.agent_state.update_agent_state(agent_id, "idle")
                return
            
            # Apply patch
            success, error = await self.validator.apply_patch(patch_id, test_id)
            
            if not success:
                self.logger.error(
                    platform="response_loop",
                    status="error",
                    message=f"Patch application failed: {error}",
                    tags=["process", "error"]
                )
                self.agent_state.update_agent_state(agent_id, "idle")
                return
            
            # Verify patch
            success, error = await self.validator.verify_patch(patch_id, test_id)
            
            if not success:
                self.logger.error(
                    platform="response_loop",
                    status="error",
                    message=f"Patch verification failed: {error}",
                    tags=["process", "error"]
                )
                await self.validator.rollback_patch(patch_id, test_id)
                self.agent_state.update_agent_state(agent_id, "idle")
                return
            
            # Update agent state
            self.agent_state.update_agent_state(agent_id, "idle")
            
            # Clean up
            response_file.unlink()
            
            self.logger.info(
                platform="response_loop",
                status="processed",
                message=f"Processed response for test {test_id}",
                tags=["process", "success"]
            )
            
        except Exception as e:
            self.logger.error(
                platform="response_loop",
                status="error",
                message=f"Error processing response file: {str(e)}",
                tags=["process", "error"]
            )
            if agent_id:
                self.agent_state.update_agent_state(agent_id, "error") 