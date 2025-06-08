"""
Example of using the LLM agent with the messaging system.
"""

import asyncio
import os
from datetime import datetime
from dreamos.core.messaging.unified_message_system import UnifiedMessageSystem, MessageMode, MessagePriority
from dreamos.core.bridge.chatgpt.bridge import ChatGPTBridge
from dreamos.core.ai.llm_agent import LLMAgent

async def main():
    # Initialize messaging system
    message_system = UnifiedMessageSystem()
    
    # Initialize ChatGPT bridge
    chatgpt_bridge = ChatGPTBridge(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create LLM agent
    llm_agent = LLMAgent(
        agent_id="llm_agent",
        message_system=message_system,
        chatgpt_bridge=chatgpt_bridge,
        system_prompt="You are a helpful AI assistant."
    )
    
    # Create a test message
    test_message = {
        "message_id": str(datetime.now().timestamp()),
        "sender_id": "user",
        "recipient_id": "llm_agent",
        "content": "What is the capital of France?",
        "mode": MessageMode.NORMAL,
        "priority": MessagePriority.NORMAL,
        "timestamp": datetime.now(),
        "metadata": {}
    }
    
    # Send message
    await message_system.send(
        to_agent=test_message["recipient_id"],
        content=test_message["content"],
        mode=test_message["mode"],
        priority=test_message["priority"],
        from_agent=test_message["sender_id"],
        metadata=test_message["metadata"]
    )
    
    # Wait for response
    await asyncio.sleep(2)
    
    # Get conversation history
    history = llm_agent.get_history()
    print("\nConversation History:")
    for msg in history:
        print(f"{msg['role']}: {msg['content']}")
    
    # Cleanup
    await llm_agent.cleanup()
    await message_system.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 
