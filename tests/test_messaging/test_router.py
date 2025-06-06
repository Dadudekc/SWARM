"""
Tests for MessageRouter
---------------------
Validates routing functionality including:
- Direct routing
- Pattern-based routing
- Mode-specific handlers
- Default handlers
"""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime
from dreamos.core.messaging.router import MessageRouter
from dreamos.core.messaging.unified_message_system import Message, MessageMode, MessagePriority

@pytest.fixture
async def router():
    """Create a router for testing."""
    router = MessageRouter()
    yield router

@pytest.mark.asyncio
async def test_direct_routing(router):
    """Test direct routing between agents."""
    msg = Message(
        message_id="test-1",
        sender_id="A",
        recipient_id="B",
        content="direct",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert success

@pytest.mark.asyncio
async def test_pattern_routing(router):
    """Test pattern-based routing."""
    # Add pattern route
    router.add_pattern_route("agent-.*", "B")
    
    msg = Message(
        message_id="test-2",
        sender_id="A",
        recipient_id="agent-1",
        content="pattern",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert success

@pytest.mark.asyncio
async def test_mode_handler(router):
    """Test mode-specific message handling."""
    handled = False
    
    async def handle_command(message: Message, target: str) -> bool:
        nonlocal handled
        handled = True
        return True
    
    # Add handler for command mode
    router.add_mode_handler(MessageMode.COMMAND, handle_command)
    
    msg = Message(
        message_id="test-3",
        sender_id="A",
        recipient_id="B",
        content="command",
        mode=MessageMode.COMMAND,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert success
    assert handled

@pytest.mark.asyncio
async def test_default_handler(router):
    """Test default message handling."""
    handled = False
    
    async def handle_default(message: Message, target: str) -> bool:
        nonlocal handled
        handled = True
        return True
    
    # Add default handler
    router.add_default_handler(handle_default)
    
    msg = Message(
        message_id="test-4",
        sender_id="A",
        recipient_id="B",
        content="default",
        mode=MessageMode.NORMAL,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert success
    assert handled

@pytest.mark.asyncio
async def test_multiple_handlers(router):
    """Test multiple handlers for a message."""
    handler1_called = False
    handler2_called = False
    
    async def handler1(message: Message, target: str) -> bool:
        nonlocal handler1_called
        handler1_called = True
        return True
    
    async def handler2(message: Message, target: str) -> bool:
        nonlocal handler2_called
        handler2_called = True
        return True
    
    # Add multiple handlers
    router.add_mode_handler(MessageMode.SYSTEM, handler1)
    router.add_mode_handler(MessageMode.SYSTEM, handler2)
    
    msg = Message(
        message_id="test-5",
        sender_id="A",
        recipient_id="B",
        content="multiple",
        mode=MessageMode.SYSTEM,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert success
    assert handler1_called
    assert handler2_called

@pytest.mark.asyncio
async def test_handler_failure(router):
    """Test handling of handler failures."""
    async def failing_handler(message: Message, target: str) -> bool:
        return False
    
    router.add_mode_handler(MessageMode.SYSTEM, failing_handler)
    
    msg = Message(
        message_id="test-6",
        sender_id="A",
        recipient_id="B",
        content="failure",
        mode=MessageMode.SYSTEM,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert not success

@pytest.mark.asyncio
async def test_remove_handlers(router):
    """Test removing handlers."""
    handled = False
    
    async def handler(message: Message, target: str) -> bool:
        nonlocal handled
        handled = True
        return True
    
    # Add and then remove handler
    router.add_mode_handler(MessageMode.SYSTEM, handler)
    router.remove_mode_handler(MessageMode.SYSTEM, handler)
    
    msg = Message(
        message_id="test-7",
        sender_id="A",
        recipient_id="B",
        content="removed",
        mode=MessageMode.SYSTEM,
        priority=MessagePriority.NORMAL,
        timestamp=datetime.now(),
        metadata={}
    )
    
    success = await router.route(msg)
    assert success
    assert not handled  # Handler should not be called 