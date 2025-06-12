"""
Example script demonstrating the Dream.OS messaging system.
"""

import asyncio
import logging
from datetime import datetime
from dreamos.core.messaging.base import Message, MessageType, MessagePriority
from dreamos.core.messaging.system import MessageSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dreamos.messaging")

async def command_handler(message: Message) -> bool:
    """Handle command messages."""
    logger.info(f"Received command: {message.content}")
    return True

async def status_handler(message: Message) -> bool:
    """Handle status messages."""
    logger.info(f"Received status: {message.content}")
    return True

async def error_handler(message: Message) -> bool:
    """Handle error messages."""
    logger.error(f"Received error: {message.content}")
    return True

async def default_handler(message: Message) -> bool:
    """Handle unknown message types."""
    logger.warning(f"Received unknown message type: {message.type}")
    return True

async def main():
    """Run the messaging system example."""
    # Create message system
    system = MessageSystem()
    
    # Configure system
    system.add_route("agent-1", {"agent-2", "agent-3"})
    system.add_route("agent-2", {"agent-1"})
    system.add_route("agent-3", {"agent-1"})
    
    system.add_handler(MessageType.COMMAND, command_handler)
    system.add_handler(MessageType.STATUS, status_handler)
    system.add_handler(MessageType.ERROR, error_handler)
    system.set_default_handler(default_handler)
    
    system.set_rate_limit("agent-1", 10, 60)  # 10 messages per minute
    system.set_content_pattern(MessageType.COMMAND, r"^cmd:.*$")
    system.set_required_fields(MessageType.STATUS, {"status_code"})
    
    # Start system
    await system.start()
    
    try:
        # Send command message
        command = Message(
            id="cmd-1",
            type=MessageType.COMMAND,
            priority=MessagePriority.HIGH,
            sender="agent-1",
            recipient="agent-2",
            content="cmd:test",
            metadata={"timestamp": datetime.now().isoformat()}
        )
        success = await system.send(command)
        logger.info(f"Command sent: {success}")
        
        # Send status message
        status = Message(
            id="status-1",
            type=MessageType.STATUS,
            priority=MessagePriority.NORMAL,
            sender="agent-2",
            recipient="agent-1",
            content="System running",
            metadata={
                "status_code": "OK",
                "timestamp": datetime.now().isoformat()
            }
        )
        success = await system.send(status)
        logger.info(f"Status sent: {success}")
        
        # Send invalid command (will be rejected)
        invalid_command = Message(
            id="cmd-2",
            type=MessageType.COMMAND,
            priority=MessagePriority.NORMAL,
            sender="agent-1",
            recipient="agent-2",
            content="invalid command",
            metadata={}
        )
        success = await system.send(invalid_command)
        logger.info(f"Invalid command sent: {success}")
        
        # Send invalid status (will be rejected)
        invalid_status = Message(
            id="status-2",
            type=MessageType.STATUS,
            priority=MessagePriority.NORMAL,
            sender="agent-2",
            recipient="agent-1",
            content="Invalid status",
            metadata={}
        )
        success = await system.send(invalid_status)
        logger.info(f"Invalid status sent: {success}")
        
        # Broadcast message
        broadcast = Message(
            id="broadcast-1",
            type=MessageType.STATUS,
            priority=MessagePriority.LOW,
            sender="agent-1",
            recipient="all",
            content="System maintenance",
            metadata={
                "status_code": "INFO",
                "timestamp": datetime.now().isoformat()
            }
        )
        count = await system.broadcast(broadcast, exclude={"agent-1"})
        logger.info(f"Broadcast sent to {count} recipients")
        
        # Wait for processing
        await asyncio.sleep(1)
        
    finally:
        # Stop system
        await system.stop()

if __name__ == "__main__":
    asyncio.run(main()) 