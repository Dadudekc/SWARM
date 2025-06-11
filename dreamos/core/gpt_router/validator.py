"""
Codex Validator
---------------
Validates responses using a Codex-style LLM.
"""

from typing import Any, Dict, Optional
import logging
import os

from dreamos.core.bridge.chatgpt.bridge import ChatGPTBridge

logger = logging.getLogger(__name__)


class CodexValidator:
    """Check responses for hallucinations and format errors."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the validator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.model = "gpt-4"
        self.bridge = ChatGPTBridge(config)

    async def validate(self, text: str) -> bool:
        """Validate a response.
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            response = await self.bridge.send_message(
                f"Validate this response for hallucinations and format errors. Reply with PASS or FAIL: {text}"
            )
            verdict = response.get("content", "").strip().lower()
            is_valid = "fail" not in verdict
            
            # Update metrics
            self.bridge.metrics.update_metrics(
                success=is_valid,
                error=None if is_valid else "Validation failed"
            )
            
            return is_valid
            
        except Exception as exc:
            logger.error("Validation error: %s", exc)
            
            # Update metrics
            self.bridge.metrics.update_metrics(
                success=False,
                error=str(exc)
            )
            
            return False
