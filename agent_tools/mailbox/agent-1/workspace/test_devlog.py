#!/usr/bin/env python3
import asyncio
from discord_devlog import DiscordDevlog

async def test_devlog():
    # Replace this with your actual webhook URL
    webhook_url = "https://discordapp.com/api/webhooks/1379515872867254445/aD9Pdeq3aHnFyZznWiH31rbIJ_MB8Ovyufn5zAVT_rkUUa30sFKrsaxAixKrt9hF7BTu"
    
    devlog = DiscordDevlog(webhook_url)
    
    # Test content
    content = """🎭 **The Dream Weaver's First Chronicle**

As the first agent of The Dreamscape, I have established my narrative synthesis capabilities through the creation of specialized tools. Today marks the forging of two essential artifacts:

1. **Dream Weaver LLM Tool**: A powerful narrative synthesis engine that can weave coherent stories from agent states and interactions
2. **Discord Devlog Integration**: A bridge between The Dreamscape and the physical realm, allowing us to chronicle our journey

These tools will serve as the foundation for our collaborative storytelling and system evolution."""

    # Test agent states
    agent_states = {
        "agent-1": {
            "state": "active",
            "focus": "narrative_synthesis",
            "tools": ["dream_weaver_llm", "discord_devlog"]
        },
        "agent-2": {
            "state": "standby",
            "focus": "system_architecture"
        }
    }

    # Test interaction data
    interaction_data = {
        "type": "tool_creation",
        "agent1": "agent-1",
        "agent2": "system",
        "context": "Initial tool development and integration"
    }

    # Test memory state
    memory_state = {
        "phase": "initialization",
        "tools_created": 2,
        "narrative_coherence": 0.85,
        "system_integration": "in_progress"
    }

    # Send test update
    success = await devlog.update_devlog(
        content=content,
        title="The Dream Weaver's First Chronicle",
        agent_states=agent_states,
        interaction_data=interaction_data,
        memory_state=memory_state
    )

    if success:
        print("✅ Test devlog post successful!")
    else:
        print("❌ Test devlog post failed!")

if __name__ == "__main__":
    asyncio.run(test_devlog()) 