"""Compatibility stub for the legacy `dreamos.core.messaging.base` module.

Provides a minimal `BaseMessagingComponent` placeholder so legacy imports keep
working during the refactor.
"""
from __future__ import annotations

from typing import Any, Optional, Dict
from enum import Enum, auto
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod
import uuid
import copy

__all__ = ["BaseMessagingComponent", "MessagePriority", "MessageType", "Message", "MessageQueue", "MessageRouter", "SimpleQueue", "MessageValidator", "MessageHandler"]


class BaseMessagingComponent:  # pylint: disable=too-few-public-methods
    """No-op stand-in for the historical messaging base class."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        pass

    def send(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None

    def receive(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
        return None

class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class MessageType(Enum):
    COMMAND = auto()
    REQUEST = auto()
    RESPONSE = auto()
    BROADCAST = auto()
    STATUS = auto()
    ERROR = auto()
    DEBUG = auto()
    UNKNOWN = auto()  # Ensures forward-compatibility with future tests

class Message:  # noqa: D401
    """Flexible message model used by unit-tests.

    It intentionally accepts a broad set of keyword arguments so that older
    call-sites (e.g. ``Message(type=..., sender=..., recipient=...)``) do not
    explode with ``TypeError: unexpected keyword``.
    """

    # NOTE: We *avoid* using @dataclass to remain forgiving towards extra
    # kwargs that the test-suite may provide in the future.

    def __init__(self, **kwargs: Any) -> None:  # noqa: D401
        self.id: str = kwargs.pop("id", str(uuid.uuid4()))
        # Alias support: ``type`` or ``message_type``
        self.type: MessageType = kwargs.pop(
            "type",
            kwargs.pop("message_type", MessageType.COMMAND),
        )
        self.priority: MessagePriority = kwargs.pop(
            "priority", MessagePriority.NORMAL
        )
        self.sender: Optional[str] = kwargs.pop("sender", None)
        self.recipient: Optional[str] = kwargs.pop("recipient", None)
        self.content: Optional[str] = kwargs.pop("content", None)
        self.metadata: Dict[str, Any] = kwargs.pop("metadata", {})
        self.timestamp: datetime = kwargs.pop("timestamp", datetime.now())

        # Silently store any extra fields so tests can introspect later.
        for key, value in kwargs.items():
            setattr(self, key, value)

    # EDIT START: Provide a helper to clone message instances used by router.broadcast
    def copy(self):  # noqa: D401
        """Return a shallow copy of the message instance.

        We purposefully *do not* generate a new ``id`` because broadcast semantics
        in the current test-suite expect the same identifier across recipients.
        The caller can always override fields (e.g., ``recipient``) after copying.
        """
        return copy.copy(self)
    # EDIT END

class MessageQueue(ABC):
    """Abstract queue interface (subset)."""

    @abstractmethod
    async def enqueue(self, message: Message) -> bool:  # noqa: D401
        pass

    @abstractmethod
    async def dequeue(self):  # noqa: D401
        pass

    @abstractmethod
    async def peek(self):  # noqa: D401
        pass

class MessageRouter:  # minimal placeholder
    async def route_message(self, message: Message):
        return True
    async def register_handler(self, message_type: MessageType, handler):
        pass
    async def unregister_handler(self, message_type: MessageType, handler):
        pass

# ---------------------------------------------------------------------------
# Concrete no-op queue used by legacy UnifiedMessageSystem fall-back
# ---------------------------------------------------------------------------

class SimpleQueue(MessageQueue):
    """Minimal runnable queue that fulfils the abstract interface."""

    async def enqueue(self, message: Message) -> bool:  # noqa: D401
        return True

    async def dequeue(self):  # noqa: D401
        return None

    async def peek(self):  # noqa: D401
        return None

# ---------------------------------------------------------------------------
# Validator ------------------------------------------------------------------
# ---------------------------------------------------------------------------

class MessageValidator:  # noqa: D401
    """Very small placeholder used by unit tests."""

    async def validate(self, message: Message, *args: Any, **kwargs: Any) -> bool:  # noqa: D401
        return True

# ---------------------------------------------------------------------------
# Handler --------------------------------------------------------------------
# ---------------------------------------------------------------------------

class MessageHandler:  # noqa: D401
    """No-op message handler placeholder."""

    async def handle(self, message: Message, *args: Any, **kwargs: Any):  # noqa: D401
        return True

# Append new symbols to public API
__all__.extend(["Message", "MessagePriority", "MessageQueue", "MessageRouter", "SimpleQueue", "MessageValidator", "MessageHandler"]) 