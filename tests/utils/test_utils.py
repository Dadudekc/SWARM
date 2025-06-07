"""
Test Utilities
------------
Common utilities for testing.
"""

import os
import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union

from tests.utils.mock_discord import (
    MockGuild,
    MockMember,
    MockRole,
    MockChannel,
    MockMessage,
    MockEmbed,
    MockWebhook,
    MockFile
)

from dreamos.core.agents.base import BaseAgent
from dreamos.core.agents.bus import AgentBus

def create_test_guild(
    guild_id: int = 1,
    name: str = "Test Guild",
    channels: Optional[list[MockChannel]] = None,
    members: Optional[list[MockMember]] = None,
    roles: Optional[list[MockRole]] = None
) -> MockGuild:
    """Create a test guild.
    
    Args:
        guild_id: Guild ID
        name: Guild name
        channels: List of channels
        members: List of members
        roles: List of roles
        
    Returns:
        Mock guild
    """
    return MockGuild(
        id=guild_id,
        name=name,
        channels=channels or [],
        members=members or [],
        roles=roles or []
    )

def create_test_member(
    member_id: int = 1,
    name: str = "Test Member",
    display_name: Optional[str] = None,
    bot: bool = False
) -> MockMember:
    """Create a test member.
    
    Args:
        member_id: Member ID
        name: Member name
        display_name: Display name
        bot: Whether member is a bot
        
    Returns:
        Mock member
    """
    return MockMember(
        id=member_id,
        name=name,
        display_name=display_name,
        bot=bot
    )

def create_test_channel(
    channel_id: int = 1,
    name: str = "test-channel",
    guild: Optional[MockGuild] = None,
    type: str = "text"
) -> MockChannel:
    """Create a test channel.
    
    Args:
        channel_id: Channel ID
        name: Channel name
        guild: Parent guild
        type: Channel type
        
    Returns:
        Mock channel
    """
    return MockChannel(
        id=channel_id,
        name=name,
        guild=guild,
        type=type
    )

def create_test_message(
    message_id: int = 1,
    content: str = "Test message",
    channel: Optional[MockChannel] = None,
    author: Optional[MockMember] = None
) -> MockMessage:
    """Create a test message.
    
    Args:
        message_id: Message ID
        content: Message content
        channel: Channel the message was sent in
        author: Message author
        
    Returns:
        Mock message
    """
    if not channel:
        channel = create_test_channel()
    if not author:
        author = create_test_member()
    
    return MockMessage(
        id=message_id,
        content=content,
        channel=channel,
        author=author
    )

def create_test_embed(
    title: Optional[str] = "Test Embed",
    description: Optional[str] = "Test description",
    color: Optional[int] = 0x00ff00
) -> MockEmbed:
    """Create a test embed.
    
    Args:
        title: Embed title
        description: Embed description
        color: Embed color
        
    Returns:
        Mock embed
    """
    return MockEmbed(
        title=title,
        description=description,
        color=color
    )

def create_test_webhook(
    webhook_id: int = 1,
    token: str = "test_token",
    url: str = "https://discord.com/api/webhooks/test",
    channel_id: int = 1,
    guild_id: Optional[int] = None,
    name: Optional[str] = None
) -> MockWebhook:
    """Create a test webhook.
    
    Args:
        webhook_id: Webhook ID
        token: Webhook token
        url: Webhook URL
        channel_id: Channel ID
        guild_id: Guild ID
        name: Webhook name
        
    Returns:
        Mock webhook
    """
    return MockWebhook(
        id=webhook_id,
        token=token,
        url=url,
        channel_id=channel_id,
        guild_id=guild_id,
        name=name
    )

def create_test_file(
    filename: str = "test.txt",
    content: str = "Test content",
    description: Optional[str] = None,
    spoiler: bool = False
) -> MockFile:
    """Create a test file.
    
    Args:
        filename: File name
        content: File content
        description: File description
        spoiler: Whether file is a spoiler
        
    Returns:
        Mock file
    """
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write(content)
        f.flush()
        return MockFile(
            filename=filename,
            fp=f,
            description=description,
            spoiler=spoiler
        )

def create_test_config(
    config_path: Union[str, Path],
    config_data: Dict[str, Any]
) -> None:
    """Create a test configuration file.
    
    Args:
        config_path: Path to config file
        config_data: Configuration data
    """
    with open(config_path, 'w') as f:
        json.dump(config_data, f, indent=2)

def cleanup_test_files(*paths: Union[str, Path]) -> None:
    """Clean up test files.
    
    Args:
        *paths: Paths to clean up
    """
    for path in paths:
        if os.path.exists(path):
            if os.path.isfile(path):
                os.unlink(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        os.unlink(os.path.join(root, name))
                    for name in dirs:
                        os.rmdir(os.path.join(root, name))
                os.rmdir(path)

def create_test_agent(
    agent_id: str = "test_agent",
    name: str = "Test Agent",
    config: Optional[Dict[str, Any]] = None
) -> BaseAgent:
    """Create a test agent.
    
    Args:
        agent_id: Agent ID
        name: Agent name
        config: Agent configuration
        
    Returns:
        Test agent instance
    """
    class TestAgent(BaseAgent):
        def __init__(self, agent_id: str, name: str, config: Optional[Dict[str, Any]] = None):
            super().__init__(agent_id, name, config)
            
        async def start(self):
            pass
            
        async def stop(self):
            pass
            
        async def process(self, message: Any) -> Any:
            return message
            
    return TestAgent(agent_id, name, config)

def create_test_agent_bus(
    bus_id: str = "test_bus",
    config: Optional[Dict[str, Any]] = None
) -> AgentBus:
    """Create a test agent bus.
    
    Args:
        bus_id: Bus ID
        config: Bus configuration
        
    Returns:
        Test agent bus instance
    """
    return AgentBus(bus_id, config)

def safe_remove(path: Union[str, Path]) -> None:
    """Safely remove a file or directory, ignoring errors."""
    try:
        p = Path(path)
        if p.is_file() or p.is_symlink():
            p.unlink()
        elif p.is_dir():
            for sub in p.iterdir():
                safe_remove(sub)
            p.rmdir()
    except Exception:
        pass

def cleanup_test_environment(*paths: Union[str, Path]) -> None:
    """Remove files and directories created during tests."""
    for path in paths:
        safe_remove(path) 