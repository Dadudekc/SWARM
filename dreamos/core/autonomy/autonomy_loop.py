"""
Autonomy Loop
------------
High-level orchestrator that wires:
    • CellPhone → ChatGPTBridge → CursorController
    • Git commit/push
    • Quality control pass
    • Health monitoring and task queue processing
"""

import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Dream.OS modules
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.request_queue import RequestQueue
from dreamos.core.monitoring.bridge_health import BridgeHealthMonitor
from dreamos.core.utils.system_ops import with_retry
from dreamos.core.ai.chatgpt_bridge import ChatGPTBridge
from dreamos.core.cursor.cursor_controller import CursorController
from dreamos.core.ai.llm_agent import LLMAgent
from dreamos.core.messaging.message_handler import MessageHandler
from agent_tools.config.config_loader import ConfigLoader

# Constants & paths
ROOT = Path(__file__).resolve().parent.parent.parent  # Go up to project root
COMMIT_MSG = "feat(autonomy): Apply ChatGPT patch & Codex-QC feedback"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("autonomy_loop")

class AutonomyLoop:
    """Main autonomy loop for Dream.OS."""
    
    def __init__(self, agent_id: str, config_path: Optional[str] = None):
        """Initialize the autonomy loop.
        
        Args:
            agent_id: Unique identifier for this agent instance
            config_path: Optional path to config file
        """
        self.agent_id = agent_id
        
        # Load configuration
        self.config_loader = ConfigLoader()
        self.config = self.config_loader.load_config(agent_id)
        
        # Set up agent-specific paths
        self.inbox = Path(self.config['inbox_path'])
        self.devlog = self.inbox.parent / "devlog.md"
        self.git_repo = ROOT
        
        # Initialize components
        self.message_handler = MessageHandler(base_dir=str(ROOT / "data" / "mailbox"))
        self.cell_phone = CellPhone(config={
            "agent_id": agent_id,
            "message_handler": self.message_handler,
            "log_level": self.config['log_level']
        })
        self.gpt_bridge = ChatGPTBridge(api_key=os.getenv("OPENAI_API_KEY"))
        self.cursor = CursorController()
        self.request_queue = RequestQueue(str(ROOT / "data" / "requests" / "queue.json"))
        self.health_monitor = BridgeHealthMonitor(str(ROOT / "data" / "health" / "status.json"))
        
        # Initialize LLM agent for ChatGPT integration
        self.llm_agent = LLMAgent(
            agent_id=agent_id,
            message_system=None,  # CellPhone does not have a message_system attribute
            chatgpt_bridge=self.gpt_bridge,
            system_prompt="You are a helpful AI coding assistant."
        )
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        
        # State
        self.running = False
        self.logger = logger
        
        # Ensure runtime directories exist
        self.inbox.parent.mkdir(parents=True, exist_ok=True)
        self.devlog.parent.mkdir(parents=True, exist_ok=True)
        
        # Log startup
        logger.info(f"Autonomy loop initialized for agent {agent_id}")
        logger.info(f"Mode: {self.config['mode']}")
        logger.info(f"Inbox path: {self.inbox}")
        logger.info(f"Log level: {self.config['log_level']}")
    
    def _handle_shutdown(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
    
    @with_retry(max_retries=3, backoff=2.0)
    async def _process_task(self, task: dict):
        """Process a single task.
        
        Args:
            task: Task to process
        """
        try:
            # Update health status
            self.health_monitor.update_health(
                is_healthy=True,
                session_active=True,
                message_count=self.health_monitor.health.message_count + 1
            )
            
            # Process task
            logger.info(f"Processing task: {task}")
            
            # Send task to ChatGPT for analysis
            response = await self.gpt_bridge.send_message(task["content"])
            
            if self.config['mode'] == 'dry-run':
                logger.info(f"[DRY RUN] Would apply changes:\n{response}")
                return
            
            # Apply the changes
            await self.cursor.apply_changes(response)
            
            # Update task status
            self.request_queue.update_task_status(task["id"], "completed")
            
            # Log completion
            self.save_devlog(f"Task {task['id']} completed")
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            self.health_monitor.update_health(
                is_healthy=False,
                error=str(e)
            )
            raise
    
    async def start(self):
        """Start the autonomy loop."""
        logger.info("Starting autonomy loop...")
        
        # Create data directories
        os.makedirs("data/requests", exist_ok=True)
        os.makedirs("data/health", exist_ok=True)
        
        # Start health monitoring
        await self.health_monitor.start()
        
        # Main loop
        self.running = True
        while self.running:
            try:
                # Check for new tasks
                tasks = self.request_queue.get_pending_requests()
                
                if tasks:
                    # Process tasks
                    for task in tasks:
                        await self._process_task(task)
                        if self.config['mode'] == 'run-once':
                            logger.info("Run once mode: exiting after processing one task")
                            self.running = False
                            break
                else:
                    # No tasks, wait a bit
                    await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def stop(self):
        """Stop the autonomy loop."""
        logger.info("Stopping autonomy loop...")
        self.running = False
        await self.health_monitor.stop()
    
    def load_tasks(self) -> Dict:
        """Load pending tasks from inbox."""
        if not self.inbox.exists():
            return {}
        try:
            with self.inbox.open() as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return {}
    
    def save_devlog(self, entry: str) -> None:
        """Save entry to development log."""
        try:
            with self.devlog.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} — {entry}\n")
        except Exception as e:
            logger.error(f"Error saving to devlog: {e}")
    
    async def push_to_git(self) -> None:
        """Commit and push changes to Git."""
        if self.config['mode'] == 'dry-run':
            logger.info("[DRY RUN] Would commit and push changes")
            return
            
        try:
            subprocess.run(["git", "-C", str(self.git_repo), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(self.git_repo), "commit", "-m", COMMIT_MSG],
                check=True
            )
            subprocess.run(["git", "-C", str(self.git_repo), "push"], check=True)
            logger.info("Git push complete")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
            raise

async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dream.OS Autonomy Loop")
    parser.add_argument("agent_id", help="Unique identifier for this agent instance")
    parser.add_argument("--config", help="Path to config file")
    
    args = parser.parse_args()
    
    loop = AutonomyLoop(
        agent_id=args.agent_id,
        config_path=args.config
    )
    
    try:
        await loop.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    finally:
        await loop.stop()

if __name__ == "__main__":
    asyncio.run(main()) 
