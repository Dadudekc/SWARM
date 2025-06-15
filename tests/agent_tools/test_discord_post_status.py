"""Tests for *agent_tools.discord.post_status* helper.

These are **offline** tests – no HTTP requests are made.  The underlying
*dreamos.discord.client.post* coroutine is monkey-patched.
"""
from __future__ import annotations

import asyncio

import importlib

import pytest

import logging


@pytest.fixture()
def discord_mod(monkeypatch):
    """Return freshly reloaded *agent_tools.discord* with patched dependencies."""

    # Import target module
    mod = importlib.import_module("agent_tools.discord")

    # Patch async poster
    posted = {
        "calls": [],  # list[tuple[url, kwargs]]
    }

    async def _fake_post(url: str, **kwargs):  # noqa: D401
        posted["calls"].append((url, kwargs))
        return True  # always succeed

    monkeypatch.setattr(mod, "_post_to_discord", _fake_post)

    # Ensure default mapping is clean – test will override as needed
    monkeypatch.setattr(mod, "DISCORD_WEBHOOKS", {}, raising=False)

    return mod, posted


def test_fallback_to_stdout_when_no_webhook(discord_mod, caplog):
    mod, posted = discord_mod

    with caplog.at_level(logging.INFO, logger="agent_tools.discord"):
        ok = mod.post_status("Agent-7", "Ping – no webhook present")

    assert ok is True
    # Should log fallback message and not attempt HTTP
    assert any("DISCORD-FALLBACK" in rec.message for rec in caplog.records)
    assert not posted["calls"]


def test_selects_correct_webhook_by_agent_digit(discord_mod, monkeypatch):
    mod, posted = discord_mod

    # Provide mapping for channel 1 (Agent-1)
    monkeypatch.setitem(mod.DISCORD_WEBHOOKS, 1, "http://example.com/webhook1")

    ok = mod.post_status("Agent-1", "Hello")
    assert ok is True

    # One HTTP call with right URL
    assert posted["calls"][0][0] == "http://example.com/webhook1" 