"""
Bridge Package
------------
Core bridge functionality for Dream.OS.
"""

from .base import BaseBridge
from .chatgpt.bridge import ChatGPTBridge

def _load_config():
    """Load bridge configuration.
    
    Returns:
        Dict containing bridge configuration
    """
    return {
        "dummy": True,
        "version": "1.0.0",
        "enabled": True
    }

__all__ = [
    'BaseBridge',
    'ChatGPTBridge',
    '_load_config'
] 