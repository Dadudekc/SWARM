"""Mock Discord Interaction components for testing."""

from typing import Optional, List, Dict, Any, Callable

class Interaction:
    """Mock Discord Interaction class."""
    
    def __init__(self, message: Any = None):
        self.message = message
        self.response = InteractionResponse(self)
        self.followup = InteractionFollowup(self)
        
    async def respond(self, *args, **kwargs):
        """Respond to the interaction."""
        return await self.response.send_message(*args, **kwargs)
        
    async def edit_original_response(self, *args, **kwargs):
        """Edit the original response."""
        return await self.response.edit_message(*args, **kwargs)
        
    async def delete_original_response(self):
        """Delete the original response."""
        return await self.response.delete_message()

class InteractionResponse:
    """Mock Discord InteractionResponse class."""
    
    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        
    async def send_message(self, *args, **kwargs):
        """Send a message response."""
        return self.interaction.message
        
    async def edit_message(self, *args, **kwargs):
        """Edit the message response."""
        return self.interaction.message
        
    async def delete_message(self):
        """Delete the message response."""
        pass

class InteractionFollowup:
    """Mock Discord InteractionFollowup class."""
    
    def __init__(self, interaction: Interaction):
        self.interaction = interaction
        
    async def send(self, *args, **kwargs):
        """Send a followup message."""
        return self.interaction.message 
