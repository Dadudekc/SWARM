"""
Prompt Router
-------------
Selects the appropriate prompt and GPT profile based on conversation context.
"""

import yaml
from pathlib import Path
from typing import Dict


class PromptRouter:
    """Decide which prompt and GPT profile to use."""

    def __init__(self, profiles_dir: Path | str = Path(__file__).parent / "profiles"):
        self.profiles_dir = Path(profiles_dir)

    def _load_profile(self, name: str) -> Dict[str, str]:
        path = self.profiles_dir / f"{name}.yaml"
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def decide_prompt(self, convo_url: str) -> Dict[str, str]:
        # Extract context from URL or conversation
        context = convo_url.lower()
        
        # Route based on context patterns
        if "analyze" in context or "pattern" in context:
            profile = self._load_profile("analyst")
        elif "log" in context or "lore" in context:
            profile = self._load_profile("dreamscribe")
        elif "error" in context or "traceback" in context:
            profile = self._load_profile("debugger")
        elif "research" in context or "compare" in context:
            profile = self._load_profile("researcher")
        elif "code" in context:
            profile = self._load_profile("codexpert")
        elif "summary" in context:
            profile = self._load_profile("summarizer")
        else:
            profile = self._load_profile("default")
            
        return profile
