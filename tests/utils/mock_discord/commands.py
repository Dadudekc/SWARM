"""
Discord Commands Mock
-------------------
Minimal mock for discord.ext.commands testing.
"""

class Bot:
    """Mock Discord bot with command support."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the bot."""
        self.commands = {}
        self.cogs = {}
    
    def command(self, *args, **kwargs):
        """Command decorator."""
        def wrapper(func):
            self.commands[func.__name__] = func
            return func
        return wrapper
    
    def run(self, *args, **kwargs):
        """Run the bot."""
        pass

__all__ = ["Bot"] 