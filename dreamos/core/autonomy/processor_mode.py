"""
Processor Mode
------------
Enumeration of processor operation modes.
"""

from enum import Enum, auto

class ProcessorMode(Enum):
    """Processor operation modes."""
    CORE = auto()
    BRIDGE = auto() 