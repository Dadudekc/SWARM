"""
Factory for creating mock Discord guilds.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class MockGuild:
    """Base mock guild class."""
    id: int
    name: str
    icon: Optional[str] = None
    icon_hash: Optional[str] = None
    splash: Optional[str] = None
    discovery_splash: Optional[str] = None
    owner_id: int = 0
    owner: bool = False
    permissions: Optional[str] = None
    region: Optional[str] = None
    afk_channel_id: Optional[int] = None
    afk_timeout: int = 300
    widget_enabled: Optional[bool] = None
    widget_channel_id: Optional[int] = None
    verification_level: int = 0
    default_message_notifications: int = 0
    explicit_content_filter: int = 0
    roles: List[Dict[str, Any]] = field(default_factory=list)
    emojis: List[Dict[str, Any]] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    mfa_level: int = 0
    application_id: Optional[int] = None
    system_channel_id: Optional[int] = None
    system_channel_flags: int = 0
    rules_channel_id: Optional[int] = None
    max_presences: Optional[int] = None
    max_members: Optional[int] = None
    vanity_url_code: Optional[str] = None
    description: Optional[str] = None
    banner: Optional[str] = None
    premium_tier: int = 0
    premium_subscription_count: Optional[int] = None
    preferred_locale: str = "en-US"
    public_updates_channel_id: Optional[int] = None
    max_video_channel_users: Optional[int] = None
    approximate_member_count: Optional[int] = None
    approximate_presence_count: Optional[int] = None
    welcome_screen: Optional[Dict[str, Any]] = None
    nsfw_level: int = 0
    stickers: List[Dict[str, Any]] = field(default_factory=list)
    premium_progress_bar_enabled: bool = False

class MockGuildFactory:
    """Factory for creating mock Discord guilds."""
    
    def __init__(self):
        """Initialize the factory."""
        self._next_id = 1
    
    def _get_next_id(self) -> int:
        """Get the next available ID."""
        id = self._next_id
        self._next_id += 1
        return id
    
    def create_basic_guild(
        self,
        name: str,
        owner_id: Optional[int] = None,
        **kwargs
    ) -> MockGuild:
        """Create a basic guild.
        
        Args:
            name: Guild name
            owner_id: Optional owner ID
            **kwargs: Additional fields to set
            
        Returns:
            MockGuild instance
        """
        owner_id = owner_id or self._get_next_id()
        
        return MockGuild(
            id=self._get_next_id(),
            name=name,
            owner_id=owner_id,
            roles=[{
                "id": self._get_next_id(),
                "name": "@everyone",
                "color": 0,
                "hoist": False,
                "position": 0,
                "permissions": "0",
                "managed": False,
                "mentionable": False
            }],
            **kwargs
        )
    
    def create_community_guild(
        self,
        name: str,
        owner_id: Optional[int] = None,
        **kwargs
    ) -> MockGuild:
        """Create a community guild with standard features.
        
        Args:
            name: Guild name
            owner_id: Optional owner ID
            **kwargs: Additional fields to set
            
        Returns:
            MockGuild instance
        """
        owner_id = owner_id or self._get_next_id()
        
        return self.create_basic_guild(
            name=name,
            owner_id=owner_id,
            features=[
                "COMMUNITY",
                "DISCOVERABLE",
                "ENABLED_DISCOVERABLE_BEFORE",
                "WELCOME_SCREEN_ENABLED"
            ],
            welcome_screen={
                "description": "Welcome to our community!",
                "welcome_channels": []
            },
            **kwargs
        )
    
    def create_partner_guild(
        self,
        name: str,
        owner_id: Optional[int] = None,
        **kwargs
    ) -> MockGuild:
        """Create a partner guild with premium features.
        
        Args:
            name: Guild name
            owner_id: Optional owner ID
            **kwargs: Additional fields to set
            
        Returns:
            MockGuild instance
        """
        owner_id = owner_id or self._get_next_id()
        
        return self.create_basic_guild(
            name=name,
            owner_id=owner_id,
            features=[
                "PARTNERED",
                "VERIFIED",
                "COMMUNITY",
                "DISCOVERABLE",
                "ENABLED_DISCOVERABLE_BEFORE",
                "WELCOME_SCREEN_ENABLED",
                "ANIMATED_ICON",
                "BANNER",
                "INVITE_SPLASH",
                "VANITY_URL"
            ],
            premium_tier=3,
            premium_subscription_count=100,
            **kwargs
        )
    
    def create_gaming_guild(
        self,
        name: str,
        owner_id: Optional[int] = None,
        **kwargs
    ) -> MockGuild:
        """Create a gaming-focused guild.
        
        Args:
            name: Guild name
            owner_id: Optional owner ID
            **kwargs: Additional fields to set
            
        Returns:
            MockGuild instance
        """
        owner_id = owner_id or self._get_next_id()
        
        return self.create_basic_guild(
            name=name,
            owner_id=owner_id,
            features=[
                "COMMUNITY",
                "DISCOVERABLE",
                "ENABLED_DISCOVERABLE_BEFORE",
                "WELCOME_SCREEN_ENABLED",
                "ANIMATED_ICON",
                "BANNER"
            ],
            welcome_screen={
                "description": "Welcome to our gaming community!",
                "welcome_channels": [
                    {
                        "channel_id": self._get_next_id(),
                        "description": "General chat",
                        "emoji_id": None,
                        "emoji_name": "💬"
                    },
                    {
                        "channel_id": self._get_next_id(),
                        "description": "Voice channels",
                        "emoji_id": None,
                        "emoji_name": "🎮"
                    }
                ]
            },
            **kwargs
        ) 