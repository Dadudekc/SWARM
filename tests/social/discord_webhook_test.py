import os
from importlib import reload

import pytest

from dreamos.social import discord_webhooks as dw


@pytest.fixture(autouse=True)
def _patch_env(monkeypatch):
    """Populate fake webhook URLs for *all* nine channels during the test run."""
    for idx in range(1, 10):
        monkeypatch.setenv(f"DISCORD_WEBHOOK_{idx}", f"https://discord.com/api/webhooks/dummy{idx}")
    # Reload the module so it re-reads environment variables.
    reload(dw)
    yield
    # No explicit teardown needed – monkeypatch restores env automatically.


def test_load_webhook_mapping_returns_nine_entries():
    """`load_webhook_mapping` should return exactly nine channel entries."""
    mapping = dw.load_webhook_mapping()
    assert len(mapping) == 9
    assert set(mapping.keys()) == set(range(1, 10))


def test_validate_webhook_mapping_accepts_valid_mapping():
    mapping = dw.load_webhook_mapping()
    assert dw.validate_webhook_mapping(mapping)


def test_mapping_has_unique_urls():
    mapping = dw.load_webhook_mapping()
    urls = list(mapping.values())
    assert len(urls) == len(set(urls)), "Webhook URLs must be unique across channels" 