"""Discord webhook utilities."""

from __future__ import annotations

import os
from typing import Dict, Optional

import requests


def load_webhook_mapping() -> Dict[int, str]:
    """Load mapping of Discord webhook channels from environment.

    Expected variables are ``DISCORD_WEBHOOK_1`` .. ``DISCORD_WEBHOOK_9``.
    Entries that are missing are skipped.
    """
    mapping: Dict[int, str] = {}
    for idx in range(1, 10):
        url = os.getenv(f"DISCORD_WEBHOOK_{idx}")
        if url:
            mapping[idx] = url
    return mapping


def validate_webhook_mapping(mapping: Dict[int, str]) -> bool:
    """Validate a webhook mapping.

    Rules:
    - Must contain exactly nine entries.
    - URLs must be unique and start with ``https://``.
    """
    if len(mapping) != 9:
        return False
    urls = list(mapping.values())
    if len(urls) != len(set(urls)):
        return False
    return all(url.startswith("https://") for url in urls)


def send_discord_message(content: str, channel: int = 1, username: Optional[str] = None) -> bool:
    """Send a simple message via Discord webhook.

    Parameters
    ----------
    content:
        Text content to send.
    channel:
        Channel number from the webhook mapping.
    username:
        Optional override for the webhook username.
    Returns
    -------
    bool
        ``True`` on successful post, ``False`` otherwise.
    """
    mapping = load_webhook_mapping()
    url = mapping.get(channel)
    if not url:
        return False
    payload = {"content": content}
    if username:
        payload["username"] = username
    try:
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 204
    except Exception:
        return False
