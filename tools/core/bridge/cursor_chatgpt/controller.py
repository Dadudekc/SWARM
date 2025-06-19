"""Control chat cycles using the browser-driven services."""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .constants import BRIDGE_INBOX, BASE_WAIT, MAX_RETRIES
from .driver import DriverManager
from .scraper import ChatScraperService
from .prompt_exec import PromptExecutionService
from .memory import AletheiaPromptManager, FeedbackEngine
from .utils import sanitize_filename

logger = logging.getLogger('chatgpt_bridge')


class ChatCycleController:
    """Master orchestrator for chat scraping and prompt cycles."""

    def __init__(
        self,
        driver_manager: Optional[DriverManager] = None,
        chat_scraper: Optional[ChatScraperService] = None,
        prompt_executor: Optional[PromptExecutionService] = None,
        feedback_engine: Optional[FeedbackEngine] = None,
        prompt_manager: Optional[AletheiaPromptManager] = None,
        config_path: str = "config.json",
        output_callback=None,
    ) -> None:
        logger.info("⚡ Initializing ChatCycleController...")

        self.output_callback = output_callback or self._default_output_callback
        self.config = self._load_config(config_path)
        self.output_dir = self.config.get("output_dir", "responses")
        self.reverse_order = self.config.get("reverse_order", False)
        self.archive_enabled = self.config.get("archive_enabled", True)

        self.driver_manager = driver_manager or DriverManager()
        # EDIT START – ensure driver is ready at construction time for better failure semantics
        # Attempt to initialise the WebDriver immediately.  This aligns runtime behaviour with
        # unit-tests that expect a *RuntimeError* if the driver cannot be created (see
        # *tests/core/bridge/test_driver_binding.py*).  It also guarantees that *driver* is
        # available for the scraper/executor wiring just below.
        _driver = self.driver_manager.setup()
        if _driver is None:
            raise RuntimeError("DriverManager.setup() returned None; unable to continue initialisation.")
        # EDIT END
        self.scraper = chat_scraper or ChatScraperService(
            self.driver_manager,
            exclusions=self.config.get("excluded_chats", []),
            reverse_order=self.reverse_order,
        )
        self.executor = prompt_executor or PromptExecutionService(self.driver_manager)
        self.feedback_engine = feedback_engine or FeedbackEngine(
            memory_file=self.config.get("memory_file", "memory/persistent_memory.json")
        )
        self.prompt_manager = prompt_manager or AletheiaPromptManager(
            memory_file=self.config.get("memory_file", "memory/persistent_memory.json")
        )

        logger.info("✅ ChatCycleController initialized.")

    def _load_config(self, config_path: str) -> dict:
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as exc:
            logger.warning("⚠️ Failed to load config: %s", exc)
            return {}

    def _default_output_callback(self, message: str) -> None:
        print(message)

    def append_output(self, message: str) -> None:
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message)

    def start(self) -> None:
        logger.info("🚀 Starting chat cycle controller...")
        self.append_output("🚀 Chat cycle starting...")
        # EDIT START – avoid re-initialising the driver if we already did so in __init__
        if self.driver_manager.driver is None:
            self.driver_manager.setup()
        # EDIT END
        if not self.scraper.validate_login():
            self.scraper.manual_login_flow()

        while True:
            try:
                self._process_pending_requests()
                time.sleep(60)
            except Exception as exc:
                logger.error("❌ Error in main loop: %s", exc)
                time.sleep(60)

    def _process_pending_requests(self) -> None:
        try:
            if not BRIDGE_INBOX.exists():
                BRIDGE_INBOX.parent.mkdir(parents=True, exist_ok=True)
                BRIDGE_INBOX.write_text("[]")
                return

            pending = json.loads(BRIDGE_INBOX.read_text())
            if pending:
                logger.info("Processing %s pending requests", len(pending))
                for req in list(pending):
                    agent_id = req.get("agent_id", "agent-unknown")
                    prompt = req.get("prompt", "")
                    if not prompt:
                        continue
                    if self._handle_request(agent_id, prompt):
                        pending.remove(req)
                        logger.info("Processed request for %s", agent_id)
                BRIDGE_INBOX.write_text(json.dumps(pending, indent=2))
        except Exception as exc:
            logger.error("Error processing requests: %s", exc)

    def _handle_request(self, agent_id: str, prompt: str) -> bool:
        attempt = 0
        wait = BASE_WAIT
        while attempt < MAX_RETRIES:
            try:
                context = {
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "memory_state": json.dumps(self.prompt_manager.memory_state, indent=2),
                }
                enhanced_prompt = self.prompt_manager.get_prompt("analyze", context)
                response = self.executor.send_prompt_and_wait(enhanced_prompt)
                if response:
                    self.prompt_manager.parse_and_update_memory(response)
                    self.feedback_engine.parse_and_update_memory(response)
                    self.feedback_engine.log_feedback(
                        prompt_name="bridge_request",
                        score=1.0,
                        hallucination=False,
                        notes=f"Response to agent {agent_id}",
                    )
                    self.feedback_engine.feedback_loop({
                        "user": agent_id,
                        "platform": "cursor_bridge",
                        "ai_output": response,
                        "timestamp": datetime.now().isoformat(),
                    })
                    self._save_response(agent_id, prompt, response)
                    return True
            except Exception as exc:
                attempt += 1
                logger.warning("Attempt %s/%s failed: %s", attempt, MAX_RETRIES, exc)
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    wait *= 2
                else:
                    self._send_error(agent_id, prompt)
                    return False
        return False

    def _save_response(self, chat_title: str, prompt_name: str, response: str) -> None:
        prompt_dir = os.path.join(
            self.output_dir,
            sanitize_filename(chat_title),
            sanitize_filename(prompt_name),
        )
        os.makedirs(prompt_dir, exist_ok=True)
        filename = (
            f"{sanitize_filename(chat_title)}_{sanitize_filename(prompt_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        file_path = os.path.join(prompt_dir, filename)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response)
            logger.info("💾 Saved response: %s", file_path)
        except Exception as exc:
            logger.error("❌ Failed to save response file %s: %s", file_path, exc)

    def _send_error(self, agent_id: str, prompt: str) -> None:
        error_msg = f"⚠️ Bridge Error: could not get ChatGPT reply for '{prompt}'"
        try:
            error_file = Path(f"messages/inbox/error_to_{agent_id}.json")
            error_data = {
                "from_agent": "chatgpt_bridge",
                "to_agent": agent_id,
                "content": error_msg,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "metadata": {
                    "type": "chatgpt_error",
                    "original_prompt": prompt,
                    "tags": ["chatgpt_response", "error"],
                },
            }
            error_file.write_text(json.dumps(error_data, indent=2))
            logger.info("Error message sent to %s", agent_id)
        except Exception as exc:
            logger.error("Failed to send error message to %s: %s", agent_id, exc)

    def shutdown(self) -> None:
        logger.info("🛑 Shutting down ChatCycleController...")
        self.feedback_engine.export_feedback_log()
        self.scraper.shutdown()


def main() -> None:
    controller = ChatCycleController()
    try:
        controller.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        controller.shutdown()

__all__ = ["ChatCycleController", "main"]
