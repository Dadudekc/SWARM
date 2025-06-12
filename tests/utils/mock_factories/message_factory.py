"""
Factory for creating mock Discord messages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class MockMessage:
    """Base mock message class."""
    id: int
    channel_id: int
    content: str = ""
    author: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    embeds: List[Dict[str, Any]] = field(default_factory=list)
    components: List[Dict[str, Any]] = field(default_factory=list)
    flags: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    edited_timestamp: Optional[datetime] = None
    tts: bool = False
    mention_everyone: bool = False
    mentions: List[Dict[str, Any]] = field(default_factory=list)
    mention_roles: List[int] = field(default_factory=list)
    pinned: bool = False
    webhook_id: Optional[int] = None
    type: int = 0  # DEFAULT
    activity: Optional[Dict[str, Any]] = None
    application: Optional[Dict[str, Any]] = None
    message_reference: Optional[Dict[str, Any]] = None
    referenced_message: Optional[Dict[str, Any]] = None

class MockMessageFactory:
    """Factory for creating mock Discord messages."""
    
    def __init__(self):
        """Initialize the factory."""
        self._next_id = 1
    
    def _get_next_id(self) -> int:
        """Get the next available ID."""
        id = self._next_id
        self._next_id += 1
        return id
    
    def create_basic_message(
        self,
        channel_id: int,
        content: str = "",
        author_id: Optional[int] = None,
        **kwargs
    ) -> MockMessage:
        """Create a basic message.
        
        Args:
            channel_id: Channel ID
            content: Message content
            author_id: Optional author ID
            **kwargs: Additional fields to set
            
        Returns:
            MockMessage instance
        """
        author = {
            "id": author_id or self._get_next_id(),
            "username": f"mock_user_{self._get_next_id()}",
            "discriminator": "0000",
            "bot": False
        }
        
        return MockMessage(
            id=self._get_next_id(),
            channel_id=channel_id,
            content=content,
            author=author,
            **kwargs
        )
    
    def create_embed_message(
        self,
        channel_id: int,
        title: str,
        description: str = "",
        color: int = 0,
        fields: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> MockMessage:
        """Create a message with an embed.
        
        Args:
            channel_id: Channel ID
            title: Embed title
            description: Embed description
            color: Embed color
            fields: Optional embed fields
            **kwargs: Additional fields to set
            
        Returns:
            MockMessage instance
        """
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "fields": fields or [],
            "type": "rich"
        }
        
        return self.create_basic_message(
            channel_id=channel_id,
            embeds=[embed],
            **kwargs
        )
    
    def create_reaction_message(
        self,
        channel_id: int,
        reactions: List[Dict[str, Any]],
        **kwargs
    ) -> MockMessage:
        """Create a message with reactions.
        
        Args:
            channel_id: Channel ID
            reactions: List of reaction data
            **kwargs: Additional fields to set
            
        Returns:
            MockMessage instance
        """
        return self.create_basic_message(
            channel_id=channel_id,
            reactions=reactions,
            **kwargs
        )
    
    def create_thread_message(
        self,
        channel_id: int,
        thread_id: Optional[int] = None,
        **kwargs
    ) -> MockMessage:
        """Create a message in a thread.
        
        Args:
            channel_id: Channel ID
            thread_id: Optional thread ID
            **kwargs: Additional fields to set
            
        Returns:
            MockMessage instance
        """
        message_reference = {
            "channel_id": channel_id,
            "message_id": thread_id or self._get_next_id()
        }
        
        return self.create_basic_message(
            channel_id=channel_id,
            message_reference=message_reference,
            **kwargs
        ) 