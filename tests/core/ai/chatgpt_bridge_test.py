"""Active functional tests for :pymod:`dreamos.core.ai.chatgpt_bridge`."""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import os
import json
from types import SimpleNamespace
from typing import Dict, Any, List

# NOTE: we *cannot* import ChatGPTBridge at module-import time because
# ``dreamos.core.ai``'s ``__init__.py`` eagerly imports a handful of heavy
# sub-modules (`dreamscribe`, `gpt_router.Router`, …) that have missing
# transitive dependencies in the trimmed test environment.  Instead we create
# *stub* modules on–the–fly **before** performing the import inside each test.

import sys
import types

import aiohttp
import pytest


def _get_bridge():
    """Return :class:`ChatGPTBridge` with upstream dependency stubs injected."""

    # Lazily create *empty* stub modules expected by ``dreamos.core.ai``
    for name in [
        "dreamos.core.ai.dreamscribe",
        "dreamos.core.ai.llm_agent",
        "dreamos.core.ai.memory_querier",
        "dreamos.core.ai.gpt_router",
        "dreamos.core.ai.gpt_router.router",
    ]:
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    # Now safely import – the stubs satisfy the references in ``__init__``
    from dreamos.core.ai.chatgpt_bridge import ChatGPTBridge  # type: ignore

    return ChatGPTBridge

# ---------------------------------------------------------------------------
# Helpers / doubles                                                         
# ---------------------------------------------------------------------------


class _DummyResponse:
    """Minimal async context-manager that mimics :class:`aiohttp.ClientResponse`."""

    def __init__(self, data: Dict[str, Any], status: int = 200):
        self._data = data
        self.status = status

    async def json(self) -> Dict[str, Any]:
        return self._data

    async def text(self) -> str:  # pragma: no cover – rarely used
        return json.dumps(self._data)

    async def __aenter__(self):  # noqa: D401 – context-manager interface
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False  # propagate exceptions


class _DummySession:
    """Fake :class:`aiohttp.ClientSession` that always returns :pydata:`_DummyResponse`."""

    def __init__(self, resp: _DummyResponse):
        self._resp = resp
        self.closed = False
        self.post_calls: List[Dict[str, Any]] = []

    def post(self, url: str, **kwargs):  # noqa: D401 – signature match
        # Record the call for later assertions
        self.post_calls.append({"url": url, **kwargs})
        return self._resp

    async def close(self):  # noqa: D401 – matches real interface
        self.closed = True


# ---------------------------------------------------------------------------
# Fixtures                                                                   
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _unset_api_key(monkeypatch):
    """Ensure *OPENAI_API_KEY* is absent for deterministic behaviour."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


# ---------------------------------------------------------------------------
# Unit tests                                                                 
# ---------------------------------------------------------------------------


def test_format_helpers_round_trip() -> None:  # noqa: D401
    """Basic *role*+*content* formatting helpers should delegate correctly."""

    bridge = _get_bridge()(api_key="dummy")

    base = bridge.format_message("test", "ping")
    assert base == {"role": "test", "content": "ping"}

    assert bridge.format_system_message("sys") == {"role": "system", "content": "sys"}
    assert bridge.format_user_message("hi") == {"role": "user", "content": "hi"}
    assert bridge.format_assistant_message("pong") == {"role": "assistant", "content": "pong"}


@pytest.mark.asyncio
async def test_chat_happy_path(monkeypatch):  # noqa: D401
    """``chat()`` returns API payload and uses the injected :class:`ClientSession`."""

    # Fake OpenAI payload
    payload = {"choices": [{"message": {"content": "Hello"}}]}

    dummy_resp = _DummyResponse(payload)
    dummy_session = _DummySession(dummy_resp)

    # Patch *aiohttp.ClientSession* constructor to return our dummy session
    monkeypatch.setattr(aiohttp, "ClientSession", lambda *a, **kw: dummy_session)

    async with _get_bridge()(api_key="dummy") as bridge:
        result = await bridge.chat([bridge.format_user_message("Hello")])

    # Assertions -----------------------------------------------------------
    assert result == payload

    # Exactly one HTTP call was made and *Authorization* header contains the token
    assert len(dummy_session.post_calls) == 1
    sent_headers = dummy_session.post_calls[0]["headers"]
    assert sent_headers["Authorization"].endswith("dummy")


def test_missing_api_key_raises():  # noqa: D401
    """Bridge *must* raise :class:`ValueError` when no API key is supplied."""

    with pytest.raises(ValueError):
        _get_bridge()(api_key=None)
