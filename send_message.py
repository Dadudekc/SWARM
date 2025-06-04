import asyncio
from dreamos.core.messaging.agent_bus import AgentBus, MessagePriority
from dreamos.core.messaging.common import MessageMode

async def send_message():
    # Initialize the agent bus
    bus = AgentBus()
    
    # Send the message
    message_id = await bus.publish(
        topic="Agent-3",
        content="success",
        sender="system",
        priority=MessagePriority.NORMAL,
        mode=MessageMode.NORMAL
    )
    
    print(f"Message sent with ID: {message_id}")

if __name__ == "__main__":
    asyncio.run(send_message()) 