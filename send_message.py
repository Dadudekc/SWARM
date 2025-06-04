import asyncio
from dreamos.core.messaging.unified_message_system import (
    UnifiedMessageSystem,
    MessagePriority,
    MessageMode,
)

async def send_message():
    # Initialize the unified message system
    ums = UnifiedMessageSystem()
    
    # Send the message
    success = await ums.send(
        to_agent="Agent-3",
        content="success",
        from_agent="system",
        priority=MessagePriority.NORMAL,
        mode=MessageMode.NORMAL,
    )

    print(f"Message sent: {success}")

if __name__ == "__main__":
    asyncio.run(send_message()) 