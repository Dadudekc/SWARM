"""
Codex Validator
---------------
Validates responses using a Codex-style LLM.
"""

from typing import Any
import logging
import os

import openai

logger = logging.getLogger(__name__)


class CodexValidator:
    """Check responses for hallucinations and format errors."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY")

    def validate(self, text: str) -> bool:
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not set; skipping validation")
            return True
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role": "user", "content": f"Validate: {text}"}],
            )
            verdict = response.choices[0].message.content.strip().lower()
            return "fail" not in verdict
        except Exception as exc:
            logger.error("Validation error: %s", exc)
            return False
