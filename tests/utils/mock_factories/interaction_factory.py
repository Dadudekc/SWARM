"""
Factory for creating mock Discord interactions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime

@dataclass
class MockInteraction:
    """Base mock interaction class."""
    id: int
    type: int
    data: Dict[str, Any] = field(default_factory=dict)
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None
    user_id: Optional[int] = None
    token: str = ""
    version: int = 1
    message: Optional[Dict[str, Any]] = None
    locale: str = "en-US"
    guild_locale: Optional[str] = None
    app_permissions: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

class MockInteractionFactory:
    """Factory for creating mock Discord interactions."""
    
    def __init__(self):
        """Initialize the factory."""
        self._next_id = 1
    
    def _get_next_id(self) -> int:
        """Get the next available ID."""
        id = self._next_id
        self._next_id += 1
        return id
    
    def create_basic_interaction(
        self,
        interaction_type: int = 2,  # Default to application command
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> MockInteraction:
        """Create a basic interaction.
        
        Args:
            interaction_type: Type of interaction (2=command, 3=component, 5=modal)
            guild_id: Optional guild ID
            channel_id: Optional channel ID
            user_id: Optional user ID
            **kwargs: Additional fields to set
            
        Returns:
            MockInteraction instance
        """
        return MockInteraction(
            id=self._get_next_id(),
            type=interaction_type,
            guild_id=guild_id,
            channel_id=channel_id,
            user_id=user_id,
            token=f"mock_token_{self._get_next_id()}",
            **kwargs
        )
    
    def create_command_interaction(
        self,
        command_name: str,
        command_id: Optional[int] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> MockInteraction:
        """Create a command interaction.
        
        Args:
            command_name: Name of the command
            command_id: Optional command ID
            options: Optional command options
            **kwargs: Additional fields to set
            
        Returns:
            MockInteraction instance
        """
        data = {
            "name": command_name,
            "id": command_id or self._get_next_id(),
            "type": 1,  # CHAT_INPUT
            "options": options or []
        }
        
        return self.create_basic_interaction(
            interaction_type=2,
            data=data,
            **kwargs
        )
    
    def create_button_interaction(
        self,
        custom_id: str,
        component_type: int = 2,  # Button
        **kwargs
    ) -> MockInteraction:
        """Create a button interaction.
        
        Args:
            custom_id: Button custom ID
            component_type: Component type (2=button)
            **kwargs: Additional fields to set
            
        Returns:
            MockInteraction instance
        """
        data = {
            "custom_id": custom_id,
            "component_type": component_type
        }
        
        return self.create_basic_interaction(
            interaction_type=3,  # MESSAGE_COMPONENT
            data=data,
            **kwargs
        )
    
    def create_modal_interaction(
        self,
        custom_id: str,
        components: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> MockInteraction:
        """Create a modal interaction.
        
        Args:
            custom_id: Modal custom ID
            components: Optional modal components
            **kwargs: Additional fields to set
            
        Returns:
            MockInteraction instance
        """
        data = {
            "custom_id": custom_id,
            "components": components or []
        }
        
        return self.create_basic_interaction(
            interaction_type=5,  # MODAL_SUBMIT
            data=data,
            **kwargs
        ) 