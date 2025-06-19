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

# stdlib imports
import asyncio
import logging
import re
from typing import Final, Optional
from pathlib import Path
import json

# Initialise logger *before* any other project imports so it's available during
# fallback handling.
logger = logging.getLogger(__name__)

# Deferred import to avoid circular issues when dreamos.discord.client depends
# on discord.py which may indirectly import this module again.
from dreamos.discord import DISCORD_WEBHOOKS, DiscordEvent, Level, make_event

# -----------------------------------------------------------------------------------------
# Network poster selection with graceful degradation
# -----------------------------------------------------------------------------------------
# 1. Try heavyweight *discord.py* async helper first (rich embed support).
# 2. If unavailable, wrap the lightweight synchronous webhook helper from
#    dreamos.discord.webhooks into an *async* shim so the public contract stays
#    unchanged for existing call-sites and unit-tests that *await* it.
# 3. As a last resort we fall back to stdout – tests rely on this path when no
#    network layer is patched.
# -----------------------------------------------------------------------------------------

from functools import partial
from typing import Any

try:
    # Primary – requires discord.py & aiohttp
    from dreamos.discord.client import post as _post_to_discord  # type: ignore[assignment]
except Exception as _imp_exc:  # noqa: BLE001 – optional dependency missing
    _post_to_discord = None  # type: ignore[assignment]

    try:
        # Secondary – lightweight synchronous helper (requests based)
        import asyncio
        import requests  # heavy but ubiquitous; already an indirect project dep

        from dreamos.discord.webhooks import send_discord_message as _sync_send  # type: ignore

        async def _post_to_discord(  # type: ignore[override]
            url: str,
            *,
            content: str = "",
            embeds: list[Any] | None = None,
        ) -> bool:
            """Async shim that POSTS raw JSON via *requests* in a thread pool."""

            payload: dict[str, Any] = {"content": content}
            if embeds:
                payload["embeds"] = embeds

            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, partial(_sync_send_raw, url, payload))

        def _sync_send_raw(target_url: str, payload: dict[str, Any]) -> bool:  # noqa: D401, ANN001
            try:
                resp = requests.post(target_url, json=payload, timeout=5)
                return resp.status_code in (200, 204)
            except Exception:
                return False

        logger.info("[agent_tools.discord] Using lightweight webhook poster (requests).")

    except Exception as _fallback_exc:  # pragma: no cover – should rarely trigger
        logger.warning(
            "[agent_tools.discord] Falling back to stdout – network helper import failed: %s | %s",
            _imp_exc,
            _fallback_exc,
        )
        _post_to_discord = None  # type: ignore[assignment]

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

    if _post_to_discord is None:
        logger.info("[DISCORD-FALLBACK stdout] %s: %s", url[:20] + "…", content)
        return True

    for attempt in range(1, _MAX_RETRIES + 1):
        ok = await _post_to_discord(url, content=content)
        if ok:
            return True
        await asyncio.sleep(0.75 * attempt)
    return False


async def _apost_embed(url: str, *, embed) -> bool:  # noqa: ANN001 – *discord.Embed*
    """Async wrapper with retries for *embed* payloads."""

    if _post_to_discord is None:
        logger.info("[DISCORD-FALLBACK stdout] %s EMBED", url[:20] + "…")
        return True

    for attempt in range(1, _MAX_RETRIES + 1):
        ok = await _post_to_discord(url, embeds=[embed])
        if ok:
            return True
        await asyncio.sleep(0.75 * attempt)
    return False


def _build_embed(agent_name: str, payload: dict):  # noqa: D401, ANN001
    """Return embed representation suitable for the active network poster.

    • If ``discord.py`` is present we leverage :class:`discord.Embed` for rich
      colouring etc.
    • Otherwise we fall back to a plain *dict* matching Discord's raw JSON
      schema so the lightweight poster can still send it.
    """

    from typing import Any

    try:
        import discord  # noqa: WPS433 – optional heavy import
    except ModuleNotFoundError:
        # ---------------------------- JSON dict path ----------------------------
        title = str(payload.get("title", f"Update from {agent_name}"))
        description = payload.get("description", "")

        default_colour = 0x2ecc71
        if any(str(f.get("value", "")).startswith("❌") for f in payload.get("fields", [])):
            default_colour = 0xe74c3c

        colour = payload.get("colour", payload.get("color", default_colour))
        if isinstance(colour, str) and colour.startswith("#"):
            colour = int(colour[1:], 16)

        return {
            "title": title,
            "description": description,
            "fields": payload.get("fields", []),
            "color": colour,
        }

    # ---------------------------- discord.py path -----------------------------
    title = str(payload.get("title", f"Update from {agent_name}"))
    description = payload.get("description")

    default_colour = 0x2ecc71
    if any(str(f.get("value", "")).startswith("❌") for f in payload.get("fields", [])):
        default_colour = 0xe74c3c

    colour = payload.get("colour", payload.get("color", default_colour))
    if isinstance(colour, str) and colour.startswith("#"):
        colour = int(colour[1:], 16)

    embed = discord.Embed(title=title, description=description or "", colour=colour)

    for f in payload.get("fields", []):
        embed.add_field(name=str(f.get("name", "-")), value=str(f.get("value", "")), inline=bool(f.get("inline", False)))

    return embed


def post_status(
    agent_name: str,
    message: str | DiscordEvent | dict,
    *,
    channel: int | None = None,
    title: str | None = None,
    footer: str | None = None,
    level: Level = "info",
) -> bool:  # noqa: D401, ANN001
    """Send a status update to Discord (or stdout fallback).

    Parameters
    ----------
    agent_name
        Source agent (used for webhook inference).
    message
        Either:
          • *str* – plain content (will be wrapped into an embed automatically).
          • *DiscordEvent* or *dict* compatible with :class:`DiscordEvent`.
    title / footer / level
        Convenience shortcuts when *message* is plain text.
    channel
        Explicit channel override (1‒9) – skips inference.
    """

    url = _resolve_webhook(agent_name, channel)
    if not url:
        logger.info("[DISCORD-FALLBACK stdout] %s: %s", agent_name, message)
        return True

    # ---------------------------- build embed -----------------------------
    payload: dict

    if isinstance(message, str):
        # Wrap plain string into standard DiscordEvent first.
        ev: DiscordEvent = make_event(
            title=title or f"Update from {agent_name}",
            body=message,
            level=level,
            agent=agent_name,
        )
        payload = _event_to_payload(ev, footer)

    elif isinstance(message, dict):
        # Dict may be raw DiscordEvent or legacy embed spec – we'll accept both.
        payload = _event_to_payload(message, footer)

    else:  # pragma: no cover – unsupported type
        logger.error("post_status(): unsupported message type %s", type(message))
        return False

    embed = _build_embed(agent_name, payload)

    async def _runner() -> bool:  # noqa: D401 – nested coroutine
        return await _apost_embed(url, embed=embed)

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


# ---------------------------------------------------------------------------
# Helper: map DiscordEvent → _build_embed payload spec
# ---------------------------------------------------------------------------


_LEVEL_COLOURS: dict[str, int] = {
    "info": 0x3498DB,   # blue
    "warn": 0xF1C40F,   # yellow
    "error": 0xE74C3C,  # red
}


def _event_to_payload(event: dict, footer: str | None = None) -> dict:  # noqa: D401, ANN001
    """Convert *DiscordEvent*-like dict into old embed builder payload format."""

    # Detect keys; if already in embed format just return.
    if "fields" in event or "description" in event:
        return event

    title = event.get("title", "Update")
    body = event.get("body", "")
    level = event.get("level", "info")
    tags = event.get("tags", [])

    description_parts = [body]
    if tags:
        description_parts.append("\n" + " ".join(f"#{t}" for t in tags))
    if footer:
        description_parts.append("\n" + footer)

    return {
        "title": title,
        "description": "\n".join(description_parts),
        "fields": [],
        "colour": _LEVEL_COLOURS.get(level, 0x2ECC71),
    } 