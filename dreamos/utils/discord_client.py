"""
Discord client imports with fallback to mocks for testing.
"""

try:
    from discord import Client
    from discord.ext.commands import Command
except ImportError:
    from tests.utils.mock_discord import Client, Command

__all__ = ["Client", "Command"] 
