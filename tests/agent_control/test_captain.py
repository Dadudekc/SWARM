import asyncio
from pathlib import Path
import importlib.util
import importlib
import sys
import types

import pytest

# Dynamically load Captain without importing heavy optional deps
CAPTAIN_PATH = Path(__file__).resolve().parents[2] / "dreamos" / "core" / "agent_control" / "captain.py"
core_stub = types.ModuleType("dreamos.core")
core_stub.__path__ = [str(CAPTAIN_PATH.parent.parent)]
agent_control_stub = types.ModuleType("dreamos.core.agent_control")
agent_control_stub.__path__ = [str(CAPTAIN_PATH.parent)]
sys.modules.setdefault("dreamos.core", core_stub)
sys.modules.setdefault("dreamos.core.agent_control", agent_control_stub)

spec = importlib.util.spec_from_file_location(
    "dreamos.core.agent_control.captain", CAPTAIN_PATH
)
captain_module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = captain_module
spec.loader.exec_module(captain_module)
Captain = captain_module.Captain
MessageSystem = importlib.import_module('dreamos.core.messaging.unified_message_system').MessageSystem
MessageMode = importlib.import_module('dreamos.core.messaging.enums').MessageMode
TaskPriority = importlib.import_module('dreamos.core.messaging.enums').TaskPriority


@pytest.mark.asyncio
async def test_assign_task_sends_message(tmp_path):
    ums = MessageSystem(runtime_dir=tmp_path)
    captain = Captain(ums=ums)

    task_id = await captain.assign_task(
        agent_id="agent1",
        name="demo",
        description="do something",
        priority=TaskPriority.HIGH,
    )

    assert task_id is not None

    messages = await ums.receive("agent1")
    assert len(messages) == 1
    msg = messages[0]
    assert msg.mode == MessageMode.TASK
    assert msg.metadata["task_id"] == task_id


@pytest.mark.asyncio
async def test_prioritize_tasks(tmp_path):
    ums = MessageSystem(runtime_dir=tmp_path)
    captain = Captain(ums=ums)

    await captain.assign_task("a1", "t1", "d1", TaskPriority.MEDIUM)
    await captain.assign_task("a2", "t2", "d2", TaskPriority.CRITICAL)
    ordered = await captain.prioritize_tasks()
    assert ordered[0]["priority"] == "CRITICAL"
