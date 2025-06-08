"""
Base Discord Mocks
----------------
Base mock classes for Discord.py testing.
"""

from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

class Cog:
    """Mock Discord Cog class."""
    def __init__(self, bot=None):
        self.bot = bot

    def cog_unload(self):
        """Unload the cog."""
        pass

class Guild:
    """Mock Discord Guild class."""
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

class Context:
    """Mock Discord Context class."""
    def __init__(self, message=None, channel=None, author=None, guild=None):
        self.message = message
        self.channel = channel
        self.author = author
        self.guild = guild

class CommandError(Exception):
    """Mock Discord CommandError class."""
    pass

@dataclass
class Command:
    """Mock Discord command."""
    name: str
    help: str = ""
    description: str = ""
    aliases: list = field(default_factory=list)
    hidden: bool = False
    enabled: bool = True
    cog: Any = None
    callback: Any = None

class Color:
    """Mock Discord Color class."""
    def __init__(self, value=0):
        self.value = value
    
    @classmethod
    def default(cls):
        return cls(0)
    
    @classmethod
    def blue(cls):
        return cls(0x3498db)
    
    @classmethod
    def red(cls):
        return cls(0xe74c3c)
    
    @classmethod
    def green(cls):
        return cls(0x2ecc71)
    
    def __int__(self):
        return self.value 
