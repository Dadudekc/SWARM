"""Memory subsystem for ChatGPT bridge."""

import os
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any

logger = logging.getLogger('chatgpt_bridge')


class AletheiaPromptManager:
    """Manage prompt templates and persistent memory."""

    def __init__(self, memory_file: str = 'memory/persistent_memory.json'):
        self.memory_file = memory_file
        self.memory_state = {
            "version": 1,
            "last_updated": None,
            "data": {}
        }
        self._lock = threading.Lock()
        logger.info(f"🧠 Aletheia initializing with memory file: {self.memory_file}")
        self._load_memory()

    def _load_memory(self) -> None:
        """Load persistent memory state from file."""
        if not os.path.exists(self.memory_file):
            logger.warning(
                f"⚠️ No memory file found at {self.memory_file}. Starting with empty memory state."
            )
            return

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.memory_state = json.load(f)
            logger.info(f"✅ Memory loaded from {self.memory_file}")
        except Exception as e:
            logger.exception(f"❌ Failed to load memory: {e}")
            self.memory_state = {"version": 1, "last_updated": None, "data": {}}

    def _save_memory(self) -> None:
        """Save current memory state to file."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(self.memory_state, f, indent=4, ensure_ascii=False)
                logger.info(f"💾 Memory saved to {self.memory_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to save memory: {e}")

    def parse_and_update_memory(self, ai_response: str) -> None:
        """Parse a MEMORY_UPDATE block from the AI response and merge it."""
        logger.info("🔍 Parsing AI response for MEMORY_UPDATE block...")

        if "MEMORY_UPDATE" not in ai_response:
            logger.warning("⚠️ No MEMORY_UPDATE block found in response.")
            return

        try:
            memory_block = ai_response.split("MEMORY_UPDATE")[-1].strip()
            json_block = memory_block[memory_block.find("{"):memory_block.rfind("}") + 1]
            updates = json.loads(json_block)
            logger.info(f"✅ Parsed MEMORY_UPDATE: {updates}")
            self._merge_memory_updates(updates)
        except Exception as e:
            logger.exception(f"❌ Failed to parse MEMORY_UPDATE block: {e}")

    def _merge_memory_updates(self, updates: dict) -> None:
        """Apply structured updates to memory state."""
        logger.info(f"🧬 Applying memory updates: {updates}")
        with self._lock:
            for key, value in updates.items():
                if isinstance(value, list):
                    self.memory_state["data"].setdefault(key, [])
                    for item in value:
                        if item not in self.memory_state["data"][key]:
                            self.memory_state["data"][key].append(item)
                else:
                    self.memory_state["data"][key] = value

            self.memory_state["version"] += 1
            self.memory_state["last_updated"] = datetime.now().isoformat()
            logger.info("✅ Memory state updated.")
        self._save_memory()

    def get_prompt(self, prompt_type: str, context: dict | None = None) -> str:
        """Return prompt text from ``prompts`` with simple template replacement."""
        prompt_file = Path(f"prompts/{prompt_type}.txt")
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

        prompt_text = prompt_file.read_text().strip()

        if context:
            for key, value in context.items():
                prompt_text = prompt_text.replace(f"{{{{ {key} }}}}", str(value))

        return prompt_text


class FeedbackEngine:
    """Parse AI responses and maintain feedback + context memory."""

    def __init__(self, memory_file: str = "memory/persistent_memory.json", feedback_log_file: str = "memory/feedback_log.json"):
        self.memory_file = memory_file
        self.feedback_log_file = feedback_log_file
        self.memory_state: Dict[str, Any] = {}
        self.feedback_log: list[dict] = []
        self.context_memory = {
            "recent_responses": [],
            "user_profiles": {},
            "platform_memories": {},
        }

        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)

        logger.info(f"🧠 FeedbackEngine initializing with memory file: {self.memory_file}")
        self._load_memory()

    def _load_memory(self) -> None:
        """Load persistent memory state from file."""
        if not os.path.exists(self.memory_file):
            logger.warning(
                f"⚠️ No memory file found at {self.memory_file}. Starting with empty memory state."
            )
            self.memory_state = {}
            return

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.memory_state = json.load(f)
            logger.info(f"✅ Memory loaded from {self.memory_file}")
        except Exception as e:
            logger.exception(f"❌ Failed to load memory: {e}")
            self.memory_state = {}

    def _save_memory(self) -> None:
        """Save current memory state to file."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(self.memory_state, f, indent=4, ensure_ascii=False)
                logger.info(f"💾 Memory saved to {self.memory_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to save memory: {e}")

    def save_memory_async(self) -> None:
        """Trigger async save using thread pool."""
        self._executor.submit(self._save_memory)

    def parse_and_update_memory(self, ai_response: str) -> None:
        """Parse MEMORY_UPDATE block from AI response and update memory."""
        logger.info("🔍 Parsing AI response for MEMORY_UPDATE block...")

        if "MEMORY_UPDATE" not in ai_response:
            logger.warning("⚠️ No MEMORY_UPDATE block found in response.")
            return

        try:
            memory_block = ai_response.split("MEMORY_UPDATE")[-1].strip()
            json_block = memory_block[memory_block.find("{"):memory_block.rfind("}") + 1]
            updates = json.loads(json_block)
            logger.info(f"✅ Parsed MEMORY_UPDATE: {updates}")
            self.apply_memory_updates(updates)
        except Exception as e:
            logger.exception(f"❌ Failed to parse MEMORY_UPDATE block: {e}")

    def apply_memory_updates(self, updates: dict) -> None:
        """Apply structured updates to memory state."""
        logger.info(f"🧬 Applying memory updates: {updates}")
        with self._lock:
            for key, value in updates.items():
                if isinstance(value, list):
                    self.memory_state.setdefault(key, [])
                    for item in value:
                        if item not in self.memory_state[key]:
                            self.memory_state[key].append(item)
                else:
                    self.memory_state[key] = value

            logger.info("✅ Memory state updated.")
        self.save_memory_async()

    def log_feedback(self, prompt_name: str, score: float, hallucination: bool, notes: str = "") -> None:
        """Record a feedback entry for reinforcement learning."""
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt_name": prompt_name,
            "score": score,
            "hallucination": hallucination,
            "notes": notes,
        }
        logger.info(f"📝 Logging feedback: {feedback_entry}")
        with self._lock:
            self.feedback_log.append(feedback_entry)

    def export_feedback_log(self) -> None:
        """Write feedback log to disk."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.feedback_log_file), exist_ok=True)
                with open(self.feedback_log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.feedback_log, f, indent=4, ensure_ascii=False)
                logger.info(f"📤 Feedback log exported to {self.feedback_log_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to export feedback log: {e}")

    def analyze_feedback(self) -> list:
        """Return prompts needing review based on low scores or hallucinations."""
        logger.info("🔎 Analyzing feedback logs for insights...")
        low_score_threshold = 0.5
        problem_prompts = [
            f["prompt_name"] for f in self.feedback_log
            if f["score"] < low_score_threshold or f["hallucination"]
        ]
        if problem_prompts:
            logger.warning(f"⚠️ Prompts needing review: {problem_prompts}")
        else:
            logger.info("✅ No major issues detected in feedback.")
        return problem_prompts

    def review_memory(self) -> Dict[str, Any]:
        """Return current memory state."""
        logger.info("📖 Reviewing memory state:")
        for key, value in self.memory_state.items():
            logger.info(f"{key}: {value}")
        return self.memory_state

    def feedback_loop(self, new_entry: Dict[str, Any]) -> None:
        """Update context memory with a new interaction entry."""
        logger.info(
            f"🔁 Feedback loop processing new entry for user {new_entry.get('user', 'unknown')}..."
        )
        user = new_entry.get("user", "unknown")
        platform = new_entry.get("platform", "general")
        ai_output = new_entry.get("ai_output", "")

        with self._lock:
            self.context_memory["recent_responses"].append(new_entry)
            if user != "unknown":
                profile = self.context_memory["user_profiles"].setdefault(
                    user, {"last_interactions": []}
                )
                profile["last_interactions"].append(new_entry)
            self.context_memory["platform_memories"].setdefault(platform, []).append(ai_output)

        logger.info(f"✅ Feedback loop updated for {user}.")
        self.save_context_memory_async()

    def save_context_memory_async(self) -> None:
        """Async save for contextual memory."""
        self._executor.submit(self.save_context_db)

    def save_context_db(self, context_file: str = "memory/context_memory.json") -> None:
        """Persist context memory to disk."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(context_file), exist_ok=True)
                with open(context_file, 'w', encoding='utf-8') as f:
                    json.dump(self.context_memory, f, indent=4, ensure_ascii=False)
                logger.info(f"💾 Context memory saved to {context_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to save context memory: {e}")

    def review_context_memory(self) -> Dict[str, Any]:
        """Return a summary of context memory."""
        logger.info("📖 Reviewing context memory:")
        for section, entries in self.context_memory.items():
            logger.info(f"{section}: {len(entries)} entries")
        return self.context_memory

__all__ = [
    "AletheiaPromptManager",
    "FeedbackEngine",
]

