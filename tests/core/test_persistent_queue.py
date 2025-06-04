import os
from tempfile import TemporaryDirectory
from pathlib import Path

from dreamos.core.persistent_queue import PersistentQueue
from dreamos.core.message import Message


def create_queue(tmpdir):
    queue_file = Path(tmpdir) / "queue.json"
    return PersistentQueue(queue_file=str(queue_file))


def test_clear_agent_removes_queue_and_history():
    with TemporaryDirectory() as tmpdir:
        queue = create_queue(tmpdir)
        queue.set_test_mode(True)

        m1 = Message(from_agent="a", to_agent="agent1", content="hi")
        m2 = Message(from_agent="a", to_agent="agent2", content="hi")
        queue.enqueue(m1)
        queue.enqueue(m2)

        queue.clear_agent("agent1")

        status = queue.get_status()
        assert all(msg.get("to_agent") != "agent1" for msg in status["messages"])

        history = queue.get_message_history()
        assert all(msg.to_agent != "agent1" for msg in history)


def test_clear_history_only_removes_specified_agent():
    with TemporaryDirectory() as tmpdir:
        queue = create_queue(tmpdir)
        queue.set_test_mode(True)

        m1 = Message(from_agent="a", to_agent="agent1", content="hi")
        m2 = Message(from_agent="a", to_agent="agent2", content="hi")
        queue.enqueue(m1)
        queue.enqueue(m2)

        queue.clear_history("agent1")

        history = queue.get_message_history()
        assert all(msg.to_agent != "agent1" for msg in history)
        # Ensure queue still contains both messages
        status = queue.get_status()
        assert len(status["messages"]) == 2
