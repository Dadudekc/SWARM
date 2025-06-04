"""Tests for the DevLog manager component."""

from pathlib import Path
from unittest.mock import AsyncMock
import sys
import types
import importlib.util

import pytest

# Mock PyQt5 to avoid optional dependency issues during import
sys.modules.setdefault("PyQt5", types.ModuleType("PyQt5"))
sys.modules.setdefault("PyQt5.QtWidgets", types.ModuleType("QtWidgets"))
mock_discord = types.ModuleType("discord")
mock_discord.Embed = object
mock_discord.Webhook = object
class _Intents:
    @staticmethod
    def all():
        return None
mock_discord.Intents = _Intents
mock_discord.Color = types.SimpleNamespace(blue=lambda: 0, green=lambda: 0)
tasks_ns = types.SimpleNamespace()
def dummy_loop(*args, **kwargs):
    def decorator(func):
        return func
    return decorator
tasks_ns.loop = dummy_loop
class DummyBot:
    def __init__(self, *args, **kwargs):
        pass

    def get_channel(self, *args, **kwargs):
        return None

    def command(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def event(self, func):
        return func

mock_discord.ext = types.SimpleNamespace(commands=types.SimpleNamespace(Bot=DummyBot), tasks=tasks_ns)
sys.modules.setdefault("discord", mock_discord)
sys.modules.setdefault("discord.ext", mock_discord.ext)
sys.modules.setdefault("discord.ext.commands", mock_discord.ext.commands)
sys.modules.setdefault("discord.ext.tasks", mock_discord.ext.tasks)
sys.modules.setdefault("aiohttp", types.ModuleType("aiohttp"))
cell_phone_stub = types.ModuleType("dreamos.core.messaging.cell_phone")
cell_phone_stub.CaptainPhone = type("CaptainPhone", (), {"__init__": lambda *_, **__: None})
cell_phone_stub.CellPhone = type("CellPhone", (), {"__init__": lambda *_, **__: None})
sys.modules["dreamos.core.messaging.cell_phone"] = cell_phone_stub
captain_phone_stub = types.ModuleType("dreamos.core.messaging.captain_phone")
captain_phone_stub.CaptainPhone = type("CaptainPhone", (), {"__init__": lambda *_, **__: None})
sys.modules["dreamos.core.messaging.captain_phone"] = captain_phone_stub
message_stub = types.ModuleType("dreamos.core.messaging.message")
message_stub.Message = object
sys.modules.setdefault("dreamos.core.messaging.message", message_stub)

DEVLOG_PATH = Path(__file__).resolve().parents[2] / "dreamos" / "core" / "agent_control" / "devlog_manager.py"
core_stub = types.ModuleType("dreamos.core")
core_stub.__path__ = []
core_stub = types.ModuleType("dreamos.core")
core_stub.__path__ = [str(DEVLOG_PATH.parent.parent)]
agent_control_stub = types.ModuleType("dreamos.core.agent_control")
agent_control_stub.__path__ = [str(DEVLOG_PATH.parent)]
sys.modules.setdefault("dreamos.core", core_stub)
sys.modules.setdefault("dreamos.core.agent_control", agent_control_stub)
spec = importlib.util.spec_from_file_location(
    "dreamos.core.agent_control.devlog_manager",
    DEVLOG_PATH,
)
devlog_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = devlog_module
spec.loader.exec_module(devlog_module)
DevLogManager = devlog_module.DevLogManager


@pytest.mark.asyncio
async def test_add_and_get_log(tmp_path: Path):
    manager = DevLogManager(runtime_dir=tmp_path)
    manager._notify_discord = AsyncMock()

    result = await manager.add_entry("agent1", "hello world")
    assert result

    content = await manager.get_log("agent1")
    assert "hello world" in content
    manager._notify_discord.assert_awaited()


@pytest.mark.asyncio
async def test_clear_log(tmp_path: Path):
    manager = DevLogManager(runtime_dir=tmp_path)
    manager._notify_discord = AsyncMock()

    await manager.add_entry("agent1", "something")
    cleared = await manager.clear_log("agent1")
    assert cleared

    content = await manager.get_log("agent1")
    assert "Log cleared" in content
