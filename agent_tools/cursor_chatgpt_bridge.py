"""
Cursor ChatGPT Bridge
Connects Cursor agents with ChatGPT using browser automation and chat scraping.
"""

import os
import time
import json
import logging
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='runtime/logs/bridge.log'
)
logger = logging.getLogger('chatgpt_bridge')

# ─────── CONFIG ───────
BRIDGE_INBOX = Path("runtime/bridge_inbox/pending_requests.json")
MAX_RETRIES = 3
BASE_WAIT = 3  # seconds
CHATGPT_URL = "https://chat.openai.com/"
# ─────────────────────

class AletheiaPromptManager:
    """
    Aletheia - Autonomous Architect of Strategic Convergence.
    Handles template-based prompt generation and memory management.
    """

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

    def _load_memory(self):
        """Load persistent memory state from file."""
        if not os.path.exists(self.memory_file):
            logger.warning(f"⚠️ No memory file found at {self.memory_file}. Starting with empty memory state.")
            return

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.memory_state = json.load(f)
            logger.info(f"✅ Memory loaded from {self.memory_file}")
        except Exception as e:
            logger.exception(f"❌ Failed to load memory: {e}")
            self.memory_state = {"version": 1, "last_updated": None, "data": {}}

    def _save_memory(self):
        """Save current memory state to file."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(self.memory_state, f, indent=4, ensure_ascii=False)
                logger.info(f"💾 Memory saved to {self.memory_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to save memory: {e}")

    def parse_and_update_memory(self, ai_response: str):
        """
        Parse MEMORY_UPDATE block from AI response and apply updates.
        Expects block in JSON format after a label like MEMORY_UPDATE.
        """
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

    def _merge_memory_updates(self, updates: dict):
        """
        Apply structured updates to memory state.
        Supports list and scalar values.
        """
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

    def get_prompt(self, prompt_type: str, context: dict = None) -> str:
        """Get prompt text from prompts directory with optional context."""
        prompt_file = Path(f"prompts/{prompt_type}.txt")
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        prompt_text = prompt_file.read_text().strip()
        
        if context:
            # Simple template replacement
            for key, value in context.items():
                prompt_text = prompt_text.replace(f"{{{{ {key} }}}}", str(value))
        
        return prompt_text

class FeedbackEngine:
    """
    FeedbackEngine - Parses AI responses, updates persistent memory,
    tracks reinforcement loops, and evolves Victor.OS intelligence.
    """

    def __init__(self, memory_file: str = "memory/persistent_memory.json", feedback_log_file: str = "memory/feedback_log.json"):
        self.memory_file = memory_file
        self.feedback_log_file = feedback_log_file
        self.memory_state = {}
        self.feedback_log = []
        self.context_memory = {
            "recent_responses": [],
            "user_profiles": {},
            "platform_memories": {}
        }

        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)

        logger.info(f"🧠 FeedbackEngine initializing with memory file: {self.memory_file}")
        self._load_memory()

    def _load_memory(self):
        """Load persistent memory state from file."""
        if not os.path.exists(self.memory_file):
            logger.warning(f"⚠️ No memory file found at {self.memory_file}. Starting with empty memory state.")
            self.memory_state = {}
            return

        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                self.memory_state = json.load(f)
            logger.info(f"✅ Memory loaded from {self.memory_file}")
        except Exception as e:
            logger.exception(f"❌ Failed to load memory: {e}")
            self.memory_state = {}

    def _save_memory(self):
        """Save current memory state to file."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
                with open(self.memory_file, 'w', encoding='utf-8') as f:
                    json.dump(self.memory_state, f, indent=4, ensure_ascii=False)
                logger.info(f"💾 Memory saved to {self.memory_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to save memory: {e}")

    def save_memory_async(self):
        """Async save operation."""
        self._executor.submit(self._save_memory)

    def parse_and_update_memory(self, ai_response: str):
        """
        Parse MEMORY_UPDATE block from AI response and apply updates.
        Expects block in JSON format after a label like MEMORY_UPDATE.
        """
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

    def apply_memory_updates(self, updates: dict):
        """
        Apply structured updates to memory state.
        Supports list and scalar values.
        """
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

    def log_feedback(self, prompt_name: str, score: float, hallucination: bool, notes: str = ""):
        """
        Logs reinforcement learning feedback per prompt execution.
        """
        feedback_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt_name": prompt_name,
            "score": score,
            "hallucination": hallucination,
            "notes": notes
        }

        logger.info(f"📝 Logging feedback: {feedback_entry}")

        with self._lock:
            self.feedback_log.append(feedback_entry)

    def export_feedback_log(self):
        """Exports feedback log to a JSON file."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.feedback_log_file), exist_ok=True)
                with open(self.feedback_log_file, 'w', encoding='utf-8') as f:
                    json.dump(self.feedback_log, f, indent=4, ensure_ascii=False)
                logger.info(f"📤 Feedback log exported to {self.feedback_log_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to export feedback log: {e}")

    def analyze_feedback(self):
        """
        Analyze feedback log for learning patterns.
        Returns prompts to review or suggestions.
        """
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

    def review_memory(self):
        """Returns current memory state."""
        logger.info("📖 Reviewing memory state:")
        for key, value in self.memory_state.items():
            logger.info(f"{key}: {value}")

        return self.memory_state

    def feedback_loop(self, new_entry: Dict[str, Any]):
        """
        Updates internal contextual memory with a new interaction.
        Includes user profiles, platform-specific memories, and recent responses.
        """
        logger.info(f"🔁 Feedback loop processing new entry for user {new_entry.get('user', 'unknown')}...")

        user = new_entry.get("user", "unknown")
        platform = new_entry.get("platform", "general")
        ai_output = new_entry.get("ai_output", "")

        with self._lock:
            # Update recent responses
            self.context_memory["recent_responses"].append(new_entry)

            # Update user profiles
            if user != "unknown":
                profile = self.context_memory["user_profiles"].setdefault(user, {"last_interactions": []})
                profile["last_interactions"].append(new_entry)

            # Update platform memories
            self.context_memory["platform_memories"].setdefault(platform, []).append(ai_output)

        logger.info(f"✅ Feedback loop updated for {user}.")
        self.save_context_memory_async()

    def save_context_memory_async(self):
        """Async save for contextual memory."""
        self._executor.submit(self.save_context_db)

    def save_context_db(self, context_file: str = "memory/context_memory.json"):
        """Save contextual memory database."""
        with self._lock:
            try:
                os.makedirs(os.path.dirname(context_file), exist_ok=True)
                with open(context_file, 'w', encoding='utf-8') as f:
                    json.dump(self.context_memory, f, indent=4, ensure_ascii=False)
                logger.info(f"💾 Context memory saved to {context_file}")
            except Exception as e:
                logger.exception(f"❌ Failed to save context memory: {e}")

    def review_context_memory(self):
        """Review context memory structure."""
        logger.info("📖 Reviewing context memory:")
        for section, entries in self.context_memory.items():
            logger.info(f"{section}: {len(entries)} entries")
        return self.context_memory

class DriverManager:
    """Manages the Chrome WebDriver instance."""
    def __init__(self):
        self.driver = None
        
    def setup(self):
        """Initialize and return a Chrome browser instance."""
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(options=options)
        return self.driver
        
    def quit(self):
        """Clean up the driver instance."""
        if self.driver:
            self.driver.quit()
            self.driver = None

class ChatScraperService:
    """
    ChatScraperService retrieves available chat titles and links from the chat UI.
    It handles exclusions and filtering for downstream execution cycles.
    """

    def __init__(self, driver_manager, exclusions=None, reverse_order=False):
        self.driver_manager = driver_manager
        self.driver = self.driver_manager.driver
        self.exclusions = exclusions if exclusions else []
        self.reverse_order = reverse_order

    def get_all_chats(self) -> list:
        """
        Retrieves all chat titles and links available in the sidebar.
        Returns a list of dictionaries with 'title' and 'link'.
        """
        logger.info("🔎 Scraping all chats from sidebar...")
        try:
            time.sleep(2)  # Give time for elements to load
            chat_elements = self.driver.find_elements("xpath", "//a[contains(@class, 'group') and contains(@href, '/c/')]")
            
            if not chat_elements:
                logger.warning("⚠️ No chats found in the sidebar.")
                return []

            chats = []
            for el in chat_elements:
                title = el.text.strip() or "Untitled"
                link = el.get_attribute("href")
                if not link:
                    logger.warning(f"⚠️ Chat '{title}' has no link, skipping.")
                    continue
                chats.append({"title": title, "link": link})

            logger.info(f"✅ Retrieved {len(chats)} chats from sidebar.")
            return chats

        except Exception as e:
            logger.error(f"❌ Error while scraping chats: {e}")
            return []

    def get_filtered_chats(self) -> list:
        """
        Filters out chats listed in self.exclusions.
        Can reverse order if self.reverse_order is True.
        """
        all_chats = self.get_all_chats()
        logger.info(f"🔍 Filtering {len(all_chats)} chats...")

        filtered = [
            chat for chat in all_chats
            if chat["title"] not in self.exclusions
        ]

        logger.info(f"✅ {len(filtered)} chats after exclusion filter.")

        if self.reverse_order:
            filtered.reverse()
            logger.info("🔄 Reversed chat order as requested.")

        return filtered

    def validate_login(self) -> bool:
        """
        Checks if the user is logged in based on the presence of sidebar elements.
        """
        logger.info("🔐 Validating OpenAI chat login status...")
        try:
            sidebar = self.driver.find_element("xpath", "//nav[contains(@class, 'flex h-full')]")
            if sidebar:
                logger.info("✅ User is logged in.")
                return True
        except Exception:
            logger.warning("⚠️ User is NOT logged in or sidebar is missing.")
        return False

    def manual_login_flow(self):
        """
        Prompts the user to manually log in via the browser.
        """
        logger.info("🛂 Manual login flow initiated. Waiting for user login...")
        self.driver.get("https://chat.openai.com/auth/login")

        while not self.validate_login():
            time.sleep(5)
            logger.info("🔄 Waiting for login...")

        logger.info("✅ Login detected! Proceeding with chat scraping.")

    def load_chat(self, chat_link: str):
        """Load a specific chat by its link."""
        try:
            self.driver.get(chat_link)
            time.sleep(2)  # Wait for chat to load
            logger.info(f"✅ Loaded chat: {chat_link}")
        except Exception as e:
            logger.error(f"❌ Failed to load chat {chat_link}: {e}")
            raise

    def archive_chat(self, chat: dict):
        """Archive a chat after processing."""
        try:
            # Click archive button if it exists
            archive_btn = self.driver.find_element("xpath", "//button[contains(@class, 'archive')]")
            if archive_btn:
                archive_btn.click()
                time.sleep(1)
                logger.info(f"✅ Archived chat: {chat.get('title', 'Untitled')}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to archive chat: {e}")

    def shutdown(self):
        """Clean shutdown of the scraper."""
        logger.info("🛑 Shutting down ChatScraperService...")
        if self.driver_manager:
            self.driver_manager.quit()

class PromptExecutionService:
    """Handles prompt execution and response retrieval."""

    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.driver = driver_manager.driver

    def get_prompt(self, prompt_name: str) -> str:
        """Get prompt text from prompts directory."""
        prompt_file = Path(f"prompts/{prompt_name}.txt")
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        return prompt_file.read_text().strip()

    def send_prompt_and_wait(self, prompt_text: str) -> str:
        """Send prompt to ChatGPT and wait for response."""
        try:
            # Wait for and find the input textarea
            textarea = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "textarea[data-id='root']"))
            )
            
            # Clear and send the prompt
            textarea.clear()
            textarea.send_keys(prompt_text)
            textarea.send_keys(Keys.ENTER)
            
            # Wait for response
            time.sleep(2)
            
            # Wait for the last message to be complete
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.result-streaming"))
            )
            
            # Get the response text
            response_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.markdown")
            if not response_elements:
                raise NoSuchElementException("No response found")
                
            return response_elements[-1].text.strip()
            
        except (TimeoutException, NoSuchElementException) as e:
            logger.error(f"Failed to get ChatGPT response: {e}")
            raise

class ChatCycleController:
    """
    Master orchestrator for chat scraping, prompt cycles,
    memory updates, and response handling.
    """

    def __init__(
        self,
        driver_manager=None,
        chat_scraper=None,
        prompt_executor=None,
        feedback_engine=None,
        prompt_manager=None,
        config_path="config.json",
        output_callback=None
    ):
        logger.info("⚡ Initializing ChatCycleController...")

        # OUTPUT HANDLING
        self.output_callback = output_callback or self._default_output_callback

        # CONFIG INITIALIZATION
        self.config = self._load_config(config_path)
        self.output_dir = self.config.get("output_dir", "responses")
        self.reverse_order = self.config.get("reverse_order", False)
        self.archive_enabled = self.config.get("archive_enabled", True)

        # SERVICES
        self.driver_manager = driver_manager or DriverManager()
        self.scraper = chat_scraper or ChatScraperService(
            self.driver_manager,
            exclusions=self.config.get("excluded_chats", []),
            reverse_order=self.reverse_order
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
        """Load configuration from file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"⚠️ Failed to load config: {e}")
            return {}

    def _default_output_callback(self, message: str):
        """Default output handler."""
        print(message)

    def append_output(self, message: str):
        """Send output to callback."""
        if self.output_callback:
            self.output_callback(message)
        else:
            print(message)

    def start(self):
        """Start the chat cycle orchestration loop."""
        logger.info("🚀 Starting chat cycle controller...")
        self.append_output("🚀 Chat cycle starting...")

        # Initialize browser and handle login
        self.driver_manager.setup()
        if not self.scraper.validate_login():
            self.scraper.manual_login_flow()

        # Process pending requests
        while True:
            try:
                self._process_pending_requests()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                time.sleep(60)  # Wait before retrying

    def _process_pending_requests(self):
        """Process any pending requests in the inbox."""
        try:
            # Load pending requests
            if not BRIDGE_INBOX.exists():
                BRIDGE_INBOX.parent.mkdir(parents=True, exist_ok=True)
                BRIDGE_INBOX.write_text("[]")
                return

            pending = json.loads(BRIDGE_INBOX.read_text())
            
            if pending:
                logger.info(f"Processing {len(pending)} pending requests")
                for req in pending:
                    agent_id = req.get("agent_id", "agent-unknown")
                    prompt = req.get("prompt", "")
                    if not prompt:
                        continue

                    # Process request
                    if self._handle_request(agent_id, prompt):
                        pending.remove(req)
                        logger.info(f"Processed request for {agent_id}")

                # Save updated pending list
                BRIDGE_INBOX.write_text(json.dumps(pending, indent=2))

        except Exception as e:
            logger.error(f"Error processing requests: {e}")

    def _handle_request(self, agent_id: str, prompt: str) -> bool:
        """Handle a single request with retries."""
        attempt = 0
        wait = BASE_WAIT

        while attempt < MAX_RETRIES:
            try:
                # Get prompt with context
                context = {
                    "agent_id": agent_id,
                    "timestamp": datetime.now().isoformat(),
                    "memory_state": json.dumps(self.prompt_manager.memory_state, indent=2)
                }
                enhanced_prompt = self.prompt_manager.get_prompt("analyze", context)
                
                response = self.executor.send_prompt_and_wait(enhanced_prompt)
                if response:
                    # Update memory with response
                    self.prompt_manager.parse_and_update_memory(response)
                    self.feedback_engine.parse_and_update_memory(response)
                    
                    # Log feedback
                    self.feedback_engine.log_feedback(
                        prompt_name="bridge_request",
                        score=1.0,  # Default score for successful response
                        hallucination=False,
                        notes=f"Response to agent {agent_id}"
                    )
                    
                    # Update context memory
                    self.feedback_engine.feedback_loop({
                        "user": agent_id,
                        "platform": "cursor_bridge",
                        "ai_output": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    self._save_response(agent_id, prompt, response)
                    return True

            except Exception as e:
                attempt += 1
                logger.warning(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(wait)
                    wait *= 2
                else:
                    self._send_error(agent_id, prompt)
                    return False

        return False

    def _save_response(self, chat_title: str, prompt_name: str, response: str):
        """Save response to file."""
        prompt_dir = os.path.join(self.output_dir, sanitize_filename(chat_title), sanitize_filename(prompt_name))
        os.makedirs(prompt_dir, exist_ok=True)

        filename = f"{sanitize_filename(chat_title)}_{sanitize_filename(prompt_name)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = os.path.join(prompt_dir, filename)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(response)
            logger.info(f"💾 Saved response: {file_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save response file {file_path}: {e}")

    def _send_error(self, agent_id: str, prompt: str):
        """Send error message to agent."""
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
                    "tags": ["chatgpt_response", "error"]
                }
            }
            error_file.write_text(json.dumps(error_data, indent=2))
            logger.info(f"Error message sent to {agent_id}")
        except Exception as e:
            logger.error(f"Failed to send error message to {agent_id}: {e}")

    def shutdown(self):
        """Clean shutdown of services."""
        logger.info("🛑 Shutting down ChatCycleController...")
        self.feedback_engine.export_feedback_log()
        self.scraper.shutdown()

def sanitize_filename(name: str) -> str:
    """Sanitize string for use in filenames."""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

def main():
    """Main entry point."""
    controller = ChatCycleController()
    try:
        controller.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        controller.shutdown()

if __name__ == "__main__":
    main() 