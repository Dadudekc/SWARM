"""
Autonomy Loop
------------
High-level orchestrator that wires:
    • CellPhone → ChatGPTBridge → CursorController
    • Git commit/push
    • StealthBrowserBridge (Codex) quality-control pass
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
from typing import Dict, Optional

# Dream.OS modules
from dreamos.core.messaging.cell_phone import CellPhone
from dreamos.core.messaging.request_queue import RequestQueue
from dreamos.core.monitoring.bridge_health import BridgeHealthMonitor
from dreamos.core.utils.system_ops import with_retry
from dreamos.core.ai.chatgpt_bridge import ChatGPTBridge
from dreamos.core.cursor_controller import CursorController
from dreamos.core.ai.llm_agent import LLMAgent
from dreamos.core.automation.browser import StealthBrowserBridge
from dreamos.core.mailbox.message_handler import MessageHandler

# Constants & paths
ROOT = Path(__file__).resolve().parent.parent.parent  # Go up to project root
INBOX = ROOT / "dreamos" / "mailbox" / "agent0" / "inbox.json"
DEVLOG = ROOT / "dreamos" / "mailbox" / "agent0" / "devlog.md"
GIT_REPO = ROOT
COMMIT_MSG = "feat(autonomy): Apply ChatGPT patch & Codex-QC feedback"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("autonomy_loop")

class AutonomyLoop:
    """Main autonomy loop for Dream.OS."""
    
    def __init__(self):
        """Initialize the autonomy loop."""
        # Initialize components
        self.message_handler = MessageHandler(base_dir=str(ROOT / "dreamos" / "mailbox"))
        self.cell_phone = CellPhone(config={
            "agent_id": "agent0",
            "message_handler": self.message_handler,
            "log_level": "INFO"
        })
        self.gpt_bridge = ChatGPTBridge(api_key=os.getenv("OPENAI_API_KEY"))
        self.cursor = CursorController()
        self.codex_bridge = StealthBrowserBridge(config_path=str(ROOT / "config" / "stealth_bridge.yaml"))
        self.request_queue = RequestQueue(str(ROOT / "data" / "requests" / "queue.json"))
        self.health_monitor = BridgeHealthMonitor(str(ROOT / "data" / "health" / "status.json"))
        
        # Initialize LLM agent for ChatGPT integration
        self.llm_agent = LLMAgent(
            agent_id="agent0",
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
        INBOX.parent.mkdir(parents=True, exist_ok=True)
        DEVLOG.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("Autonomy loop initialized")
    
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
            
            # TODO: Implement task processing logic
            # This is where you would:
            # 1. Send task to ChatGPT for analysis
            # 2. Use Codex to implement changes
            # 3. Update task status
            
            await asyncio.sleep(1)  # Simulate work
            
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
        # os.makedirs("data/messages", exist_ok=True)
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
        if not INBOX.exists():
            return {}
        try:
            with INBOX.open() as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return {}
    
    def save_devlog(self, entry: str) -> None:
        """Save entry to development log."""
        try:
            with DEVLOG.open("a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} — {entry}\n")
        except Exception as e:
            logger.error(f"Error saving to devlog: {e}")
    
    async def push_to_git(self) -> None:
        """Commit and push changes to Git."""
        try:
            subprocess.run(["git", "-C", str(GIT_REPO), "add", "."], check=True)
            subprocess.run(
                ["git", "-C", str(GIT_REPO), "commit", "-m", COMMIT_MSG],
                check=True
            )
            subprocess.run(["git", "-C", str(GIT_REPO), "push"], check=True)
            logger.info("Git push complete")
        except subprocess.CalledProcessError as e:
            logger.error(f"Git operation failed: {e}")
            raise
    
    async def quality_control(self, code_snippet: str) -> str:
        """Get Codex review of code snippet."""
        try:
            review_prompt = (
                "Codex, review this code for duplication, bloat, and obvious bugs. "
                "Respond with concise bullet-point feedback only.\n\n```python\n"
                f"{code_snippet}\n```"
            )
            
            # Use StealthBrowserBridge's send_message method
            response = await self.codex_bridge.send_message(review_prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"Codex review failed: {e}")
            return f"Error getting Codex review: {e}"
    
    def paste_to_cursor(self, content: str) -> None:
        """Paste content into Cursor editor."""
        try:
            # Use CursorController's type_text method
            self.cursor.type_text(content)
            time.sleep(0.5)  # Small delay
            self.cursor.press_ctrl_s()  # Save file
            logger.info("Response pasted into Cursor")
        except Exception as e:
            logger.error(f"Failed to paste to Cursor: {e}")
            raise
    
    async def process_task(self, task_id: str, task: Dict) -> None:
        """Process a single task."""
        try:
            prompt = task.get("prompt")
            if not prompt:
                logger.warning(f"Task {task_id} has no prompt")
                return
            
            # 1. Send prompt to ChatGPT via LLM agent
            response = await self.llm_agent.chatgpt_bridge.chat([
                self.llm_agent.chatgpt_bridge.format_system_message(
                    self.llm_agent.system_prompt
                ),
                self.llm_agent.chatgpt_bridge.format_user_message(prompt)
            ])
            response_content = response["choices"][0]["message"]["content"]
            
            # 2. Paste into Cursor
            self.paste_to_cursor(response_content)
            
            # 3. Commit & push
            await self.push_to_git()
            
            # 4. Get Codex review
            feedback = await self.quality_control(response_content)
            
            # 5. Send feedback to agent
            await self.cell_phone.send_message(
                to_agent="agent0",
                content=feedback,
                mode="NORMAL",
                from_agent="codex_reviewer"
            )
            
            # 6. Log completion
            self.save_devlog(
                f"Task {task_id} completed. Codex feedback:\n{feedback}\n{'-'*40}"
            )
            
            # 7. Mark task as done
            task["status"] = "COMPLETED"
            
        except Exception as e:
            logger.error(f"Error processing task {task_id}: {e}")
            task["status"] = "FAILED"
            task["error"] = str(e)

async def main():
    """Main entry point."""
    try:
        # Create and start autonomy loop
        loop = AutonomyLoop()
        await loop.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        # Clean up
        if 'loop' in locals():
            await loop.stop()

if __name__ == "__main__":
    asyncio.run(main()) 
