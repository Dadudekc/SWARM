"""
Factory for creating mock Discord channels.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class MockChannel:
    """Base mock channel class."""
    id: int
    type: int  # 0 = text, 2 = voice, 4 = category, etc.
    name: str
    guild_id: Optional[int] = None
    position: int = 0
    permission_overwrites: List[Dict[str, Any]] = field(default_factory=list)
    nsfw: bool = False
    topic: Optional[str] = None
    last_message_id: Optional[int] = None
    bitrate: Optional[int] = None
    user_limit: Optional[int] = None
    rate_limit_per_user: int = 0
    recipients: List[Dict[str, Any]] = field(default_factory=list)
    icon: Optional[str] = None
    owner_id: Optional[int] = None
    application_id: Optional[int] = None
    parent_id: Optional[int] = None
    last_pin_timestamp: Optional[datetime] = None
    rtc_region: Optional[str] = None
    video_quality_mode: Optional[int] = None
    message_count: int = 0
    member_count: Optional[int] = None
    thread_metadata: Optional[Dict[str, Any]] = None
    member: Optional[Dict[str, Any]] = None
    default_auto_archive_duration: Optional[int] = None
    permissions: Optional[str] = None
    flags: int = 0
    total_message_sent: int = 0
    available_tags: List[Dict[str, Any]] = field(default_factory=list)
    applied_tags: List[int] = field(default_factory=list)
    default_reaction_emoji: Optional[Dict[str, Any]] = None
    default_thread_rate_limit_per_user: int = 0
    default_sort_order: Optional[int] = None
    default_forum_layout: int = 0

class MockChannelFactory:
    """Factory for creating mock Discord channels."""
    
    def __init__(self):
        """Initialize the factory."""
        self._next_id = 1
    
    def _get_next_id(self) -> int:
        """Get the next available ID."""
        id = self._next_id
        self._next_id += 1
        return id
    
    def create_text_channel(
        self,
        guild_id: int,
        name: str,
        **kwargs
    ) -> MockChannel:
        """Create a text channel.
        
        Args:
            guild_id: Guild ID
            name: Channel name
            **kwargs: Additional fields to set
            
        Returns:
            MockChannel instance
        """
        return MockChannel(
            id=self._get_next_id(),
            type=0,  # TEXT
            name=name,
            guild_id=guild_id,
            **kwargs
        )
    
    def create_voice_channel(
        self,
        guild_id: int,
        name: str,
        bitrate: int = 64000,
        user_limit: Optional[int] = None,
        **kwargs
    ) -> MockChannel:
        """Create a voice channel.
        
        Args:
            guild_id: Guild ID
            name: Channel name
            bitrate: Channel bitrate
            user_limit: Optional user limit
            **kwargs: Additional fields to set
            
        Returns:
            MockChannel instance
        """
        return MockChannel(
            id=self._get_next_id(),
            type=2,  # VOICE
            name=name,
            guild_id=guild_id,
            bitrate=bitrate,
            user_limit=user_limit,
            **kwargs
        )
    
    def create_category(
        self,
        guild_id: int,
        name: str,
        **kwargs
    ) -> MockChannel:
        """Create a category channel.
        
        Args:
            guild_id: Guild ID
            name: Category name
            **kwargs: Additional fields to set
            
        Returns:
            MockChannel instance
        """
        return MockChannel(
            id=self._get_next_id(),
            type=4,  # CATEGORY
            name=name,
            guild_id=guild_id,
            **kwargs
        )
    
    def create_thread(
        self,
        guild_id: int,
        name: str,
        parent_id: int,
        **kwargs
    ) -> MockChannel:
        """Create a thread channel.
        
        Args:
            guild_id: Guild ID
            name: Thread name
            parent_id: Parent channel ID
            **kwargs: Additional fields to set
            
        Returns:
            MockChannel instance
        """
        return MockChannel(
            id=self._get_next_id(),
            type=11,  # PUBLIC_THREAD
            name=name,
            guild_id=guild_id,
            parent_id=parent_id,
            thread_metadata={
                "archived": False,
                "auto_archive_duration": 1440,
                "archive_timestamp": datetime.now().isoformat(),
                "locked": False,
                "invitable": True
            },
            **kwargs
        )
    
    def create_dm_channel(
        self,
        recipient_id: int,
        **kwargs
    ) -> MockChannel:
        """Create a DM channel.
        
        Args:
            recipient_id: Recipient user ID
            **kwargs: Additional fields to set
            
        Returns:
            MockChannel instance
        """
        return MockChannel(
            id=self._get_next_id(),
            type=1,  # DM
            name="Direct Message",
            recipients=[{
                "id": recipient_id,
                "username": f"mock_user_{recipient_id}",
                "discriminator": "0000",
                "bot": False
            }],
            **kwargs
        ) 