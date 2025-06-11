"""
Processor Mode Module
------------------
Defines the modes that processors can operate in.
"""

from enum import Enum, auto

class ProcessorMode(Enum):
    """Processor operation modes."""
    
    CORE = auto()  # Core system processor
    BRIDGE = auto()  # Bridge processor
    AUTONOMY = auto()  # Autonomy processor
    DEBUG = auto()  # Debug processor 