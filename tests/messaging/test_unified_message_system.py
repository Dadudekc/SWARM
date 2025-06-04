"""Integration tests for the UnifiedMessageSystem."""

import asyncio
import pytest
import sys
import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parents[2] / "dreamos" / "core" / "messaging" / "unified_message_system.py"


def load_ums():
    spec = importlib.util.spec_from_file_location("unified_message_system", module_path)
    ums = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ums)
    # Reset the singleton instance to ensure isolation between tests
    ums.MessageSystem._instance = None
    return ums


def test_send_and_receive(tmp_path):
    ums_module = load_ums()
    UnifiedMessageSystem = ums_module.UnifiedMessageSystem
    MessageMode = ums_module.MessageMode
    MessagePriority = ums_module.MessagePriority

    ums = UnifiedMessageSystem(runtime_dir=tmp_path)
    asyncio.run(ums.send(
        to_agent="Agent-Test",
        content="hello",
        from_agent="tester",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
    ))
    messages = asyncio.run(ums.receive("Agent-Test"))
    assert len(messages) == 1
    msg = messages[0]
    assert msg.content == "hello"
    assert msg.sender_id == "tester"

