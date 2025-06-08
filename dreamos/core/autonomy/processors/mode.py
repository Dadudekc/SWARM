"""
Processor Mode Enum

Defines the different modes for response processors.
"""

from enum import Enum, auto

class ProcessorMode(Enum):
    """Enum for response processor modes."""
    CORE = auto()
    TEST = auto()
    DEBUG = auto()
    PRODUCTION = auto() 