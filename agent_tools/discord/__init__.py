"""Discord bridge helpers accessible to any *agent_tools* consumer.

This thin wrapper re-uses the **centralised** :pymod:`dreamos.discord` package
so we do *not* duplicate webhook logic.  It exposes a single convenience
function::

    from agent_tools.discord import post_status

    post_status("Agent-3", "✅ Ready for duty")

The helper chooses a webhook as follows – adhering to the existing
environment-variable convention – and falls back to stdout if nothing is
configured so callers never crash in dev environments:

1.  Explicit *channel* argument (1‒9) if provided.
2.  If *agent_name* contains a digit (e.g. ``Agent-4``) that number is used.
3.  Default to channel **9** (global ops / announcements).
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Final, Optional
from pathlib import Path
import json

from dreamos.discord import DISCORD_WEBHOOKS
from dreamos.discord.client import post as _post_to_discord


logger = logging.getLogger(__name__)

__all__: list[str] = [
    "post_status",
]

_DEFAULT_CHANNEL: Final[int] = 9
_MAX_RETRIES: Final[int] = 3


# ---------------------------------------------------------------------------
# Optional disk-based mapping override
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path("config/discord_channels.json")


def _load_custom_mapping() -> dict[str, str]:
    """Return ``{agent_name: webhook}`` mapping if config file exists."""

    if not _CONFIG_PATH.is_file():
        return {}
    try:
        data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):  # pragma: no cover – misconfig
            raise ValueError("discord_channels.json must contain an object mapping")
        return {str(k): str(v) for k, v in data.items()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load %s: %s", _CONFIG_PATH, exc)
        return {}


_CUSTOM_MAPPING: dict[str, str] = _load_custom_mapping()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _infer_channel(agent_name: str) -> int | None:
    """Return channel index extracted from *agent_name* (Agent-3 → 3)."""

    match = re.search(r"(\d+)", agent_name)
    if match:
        idx = int(match.group(1))
        if 1 <= idx <= 8:  # per-agent channels 1‒8
            return idx
    return None


def _resolve_webhook(agent_name: str, channel: int | None = None) -> str:
    """Determine webhook URL from *channel* override or *agent_name*."""

    # 1) explicit channel arg always wins (env mapping)
    if channel is not None:
        return DISCORD_WEBHOOKS.get(channel, "")

    # 2) per-agent mapping via config file
    if agent_name in _CUSTOM_MAPPING:
        return _CUSTOM_MAPPING[agent_name]

    # 3) default from config file
    if "default" in _CUSTOM_MAPPING:
        return _CUSTOM_MAPPING["default"]

    # 4) fallback to env mapping using digit inference
    ch = _infer_channel(agent_name) or _DEFAULT_CHANNEL
    return DISCORD_WEBHOOKS.get(ch, "")


# ---------------------------------------------------------------------------
# Async helpers (content vs embed)
# ---------------------------------------------------------------------------

async def _apost_content(url: str, *, content: str) -> bool:
    """Async wrapper with simple retry/backoff (max 3 tries) for *content* only."""

    for attempt in range(1, _MAX_RETRIES + 1):
        ok = await _post_to_discord(url, content=content)
        if ok:
            return True
        await asyncio.sleep(0.75 * attempt)
    return False


async def _apost_embed(url: str, *, embed) -> bool:  # noqa: ANN001 – *discord.Embed*
    """Async wrapper with retries for *embed* payloads."""

    for attempt in range(1, _MAX_RETRIES + 1):
        ok = await _post_to_discord(url, embeds=[embed])
        if ok:
            return True
        await asyncio.sleep(0.75 * attempt)
    return False


def _build_embed(agent_name: str, payload: dict) -> "discord.Embed":  # noqa: D401
    """Return *discord.Embed* built from *payload* dict.

    Supported keys:
        title (str) – embed title
        description (str) – optional main body
        fields (list[dict]) – each mapping must have *name*, *value* and
            optional *inline* boolean.
        colour / color (int | str) – discord.Colour value or int hex.
    """

    import discord  # local import to avoid heavy dependency at module import

    title = str(payload.get("title", f"Update from {agent_name}"))
    description = payload.get("description")

    # Default colour green (success) unless explicit or failed status found
    default_colour = 0x2ecc71  # green
    if any(str(f.get("value", "")).startswith("❌") for f in payload.get("fields", [])):
        default_colour = 0xe74c3c  # red

    colour = payload.get("colour", payload.get("color", default_colour))
    # If colour is str like "#aabbcc" convert to int
    if isinstance(colour, str) and colour.startswith("#"):
        colour = int(colour[1:], 16)

    embed = discord.Embed(title=title, description=description or "", colour=colour)

    for f in payload.get("fields", []):
        embed.add_field(name=str(f.get("name", "-")), value=str(f.get("value", "")), inline=bool(f.get("inline", False)))

    return embed


def post_status(agent_name: str, message, *, channel: Optional[int] = None) -> bool:  # noqa: D401, ANN001
    """Post *message* to Discord.

    *message* may be either a *str* (simple content) **or** a *dict* describing
    an embed.  Structured payloads enable richer formatting without requiring
    callers to know Discord's embed API.
    """

    url = _resolve_webhook(agent_name, channel)
    if not url:
        logger.info("[DISCORD-FALLBACK stdout] %s: %s", agent_name, message)
        return True

    if isinstance(message, str):
        async def _runner() -> bool:  # noqa: D401 – nested coroutine
            content = f"**{agent_name}** – {message}"
            return await _apost_content(url, content=content)
    elif isinstance(message, dict):
        embed = _build_embed(agent_name, message)

        async def _runner() -> bool:  # noqa: D401
            return await _apost_embed(url, embed=embed)
    else:  # pragma: no cover – unsupported type
        logger.error("post_status(): unsupported message type %s", type(message))
        return False

    try:
        # If inside an existing event loop schedule a task instead of blocking.
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_runner())
            return True
    except RuntimeError:
        # No running loop – we'll create one below
        pass

    return asyncio.run(_runner()) 