"""
Formats devlog content for different social media platforms.
Handles character limits, emojis, tags, and platform-specific formatting.
Uses dream-core tone: stream-of-consciousness, lowercase, drifting sign-offs.
"""

import re
import random
import textwrap
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

from dreamos.core.utils.logging_utils import get_logger

logger = get_logger(__name__)

class SocialFormatter:
    """Formats content for different social media platforms."""
    
    # Platform-specific limits and rules
    PLATFORM_RULES = {
        "twitter": {
            "max_length": 280,
            "allow_links": True,
            "allow_hashtags": True,
            "allow_mentions": True,
            "allow_emojis": True,
            "link_length": 23,  # Twitter's t.co link length
            "truncate_marker": "..."
        },
        "reddit": {
            "max_length": 40000,
            "allow_links": True,
            "allow_hashtags": False,
            "allow_mentions": False,
            "allow_emojis": True,
            "title_max_length": 300,
            "truncate_marker": "..."
        },
        "discord": {
            "max_length": 2000,
            "allow_links": True,
            "allow_hashtags": True,
            "allow_mentions": True,
            "allow_emojis": True,
            "allow_code_blocks": True,
            "truncate_marker": "..."
        },
        "instagram": {
            "max_length": 2200,
            "allow_links": False,
            "allow_hashtags": True,
            "allow_mentions": True,
            "allow_emojis": True,
            "truncate_marker": "..."
        },
        "linkedin": {
            "max_length": 3000,
            "allow_links": True,
            "allow_hashtags": True,
            "allow_mentions": True,
            "allow_emojis": True,
            "truncate_marker": "..."
        }
    }
    
    # Dream-core vibe palettes
    EMOJIS_HEADLINE = ["🧠", "🛰️", "🚀", "🛠️", "⚙️", "🌀"]
    EMOJIS_LIST = ["•", "→", "⤷", "↪︎"]
    SIGN_OFF = [
        "crawling back in the cave...",
        "lights off, code running...",
        "system's looping, i'm ghost...",
        "dream out 🟣",
    ]
    
    LINE_WRAP = 88  # max width for long-form platforms
    
    def __init__(self):
        self.templates = self._load_templates()
        
    def _load_templates(self) -> Dict[str, str]:
        """Load platform-specific templates."""
        template_path = Path("dreamos/social/templates")
        templates = {}
        
        if template_path.exists():
            for file in template_path.glob("*.tpl"):
                platform = file.stem.replace("_post", "")
                try:
                    with open(file, 'r') as f:
                        templates[platform] = f.read().strip()
                except Exception as e:
                    logger.error("Failed to load template %s: %s", file, e)
                    
        return templates
        
    def _wrap(self, txt: str) -> str:
        """Wrap text to max width."""
        return "\n".join(textwrap.wrap(txt, self.LINE_WRAP))
        
    def _splice(self, *chunks) -> str:
        """Glue chunks with ellipses & trim double-spaces."""
        return " ... ".join(c.strip() for c in chunks if c).replace("  ", " ")
        
    def _format_links(self, text: str, platform: str) -> str:
        """Format links according to platform rules."""
        if not self.PLATFORM_RULES[platform]["allow_links"]:
            return re.sub(r'https?://\S+', '', text)
        return text
        
    def _format_hashtags(self, text: str, platform: str) -> str:
        """Format hashtags according to platform rules."""
        if not self.PLATFORM_RULES[platform]["allow_hashtags"]:
            return re.sub(r'#\w+', '', text)
        return text
        
    def _format_mentions(self, text: str, platform: str) -> str:
        """Format mentions according to platform rules."""
        if not self.PLATFORM_RULES[platform]["allow_mentions"]:
            return re.sub(r'@\w+', '', text)
        return text
        
    def _format_emojis(self, text: str, platform: str) -> str:
        """Format emojis according to platform rules."""
        if not self.PLATFORM_RULES[platform]["allow_emojis"]:
            # Remove emoji characters
            return re.sub(r'[\U0001F300-\U0001F9FF]', '', text)
        return text
        
    def _truncate_text(self, text: str, platform: str) -> str:
        """Truncate text to platform's max length."""
        max_length = self.PLATFORM_RULES[platform]["max_length"]
        marker = self.PLATFORM_RULES[platform]["truncate_marker"]
        
        if len(text) <= max_length:
            return text
            
        # Try to truncate at word boundary
        truncated = text[:max_length - len(marker)]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
            
        return truncated + marker
        
    def _format_dream_core(self, platform: str, data: Dict) -> str:
        """Format content in dream-core style."""
        now = datetime.now().strftime("%b %d %Y")
        head_emoji = random.choice(self.EMOJIS_HEADLINE)
        
        if platform.lower() in {"twitter", "x"}:
            body = self._splice(
                data.get("title", ""),
                data.get("what", ""),
                f"blocker? {data['blockers']}" if data.get("blockers") else "",
                f"next >>> {data['next']}" if data.get("next") else "",
                data.get("insight", "")
            )
            tweet = f"{head_emoji} {body[:275]} {random.choice(self.SIGN_OFF)}"
            return tweet
            
        # Long-form (Reddit / Discord / blog)
        bullet = random.choice(self.EMOJIS_LIST)
        lines = [
            f"{head_emoji} **{data.get('title', '')}** // {now}",
            "",
            f"{bullet} {self._wrap(data.get('what', ''))}",
        ]
        
        if data.get("blockers"):
            lines.append(f"{bullet} blocker → {self._wrap(data['blockers'])}")
        if data.get("next"):
            lines.append(f"{bullet} next up → {self._wrap(data['next'])}")
        lines.append("")
        if data.get("insight"):
            lines.append(f"💡 {self._wrap(data['insight'])}")
        lines.append(f"\n_{random.choice(self.SIGN_OFF)}_")
        
        return "\n".join(lines)
        
    def format_post(self, platform: str, devlog_data: Dict) -> str:
        """Format devlog content for specific platform."""
        if platform not in self.PLATFORM_RULES:
            logger.error("Unsupported platform: %s", platform)
            return str(devlog_data)
            
        try:
            # Format in dream-core style
            content = self._format_dream_core(platform, devlog_data)
            
            # Apply platform-specific formatting
            content = self._format_links(content, platform)
            content = self._format_hashtags(content, platform)
            content = self._format_mentions(content, platform)
            content = self._format_emojis(content, platform)
            
            # Truncate if needed
            content = self._truncate_text(content, platform)
            
            return content
            
        except Exception as e:
            logger.exception("Error formatting content for %s: %s", platform, e)
            return str(devlog_data)
            
    def format_title(self, platform: str, title: str) -> str:
        """Format title for platforms that support it (e.g., Reddit)."""
        if platform not in self.PLATFORM_RULES:
            return title
            
        # Prefer explicit *title_max_length* if supplied, otherwise fall back
        # to the generic ``max_length`` so that platforms like *Twitter*—which
        # have a hard character limit but no dedicated title rule—still honour
        # the constraint.  This change fixes unit-tests that expect
        # ``format_title('twitter', long_title)`` to truncate to <= 280 chars.

        max_length = (
            self.PLATFORM_RULES[platform].get("title_max_length")
            or self.PLATFORM_RULES[platform]["max_length"]
        )

        if len(title) <= max_length:
            return title
            
        marker = self.PLATFORM_RULES[platform]["truncate_marker"]
        truncated = title[:max_length - len(marker)]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            truncated = truncated[:last_space]
            
        return truncated + marker 