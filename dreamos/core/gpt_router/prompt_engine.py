"""
ChatGPT Prompt Engine
---------------------
Coordinates scraping, routing and optional Codex validation.
"""

import time
from typing import Dict

from .prompt_router import PromptRouter


class ChatGPTPromptEngine:
    """Orchestrates prompt delivery and response collection."""

    def __init__(self, scraper, codex=None):
        self.scraper = scraper
        self.validator = codex
        self.router = PromptRouter()

    def process_conversation(self, convo_url: str) -> Dict[str, str]:
        self.scraper.driver.get(convo_url)
        time.sleep(2)

        routing = self.router.decide_prompt(convo_url)
        prompt = routing["prompt"]
        target_gpt = routing["gpt_profile"]

        self.scraper.switch_to_gpt(target_gpt)
        self.scraper.send_prompt(prompt)

        reply = self.scraper.extract_latest_reply(wait_for_completion=True)

        validated = self.validator.validate(reply) if self.validator else True

        return {
            "url": convo_url,
            "prompt": prompt,
            "reply": reply,
            "gpt": target_gpt,
            "validated": validated,
        }
