"""
Bridge Package
------------
Core bridge functionality for Dream.OS.
"""

from .base import BaseBridge
from .chatgpt.bridge import ChatGPTBridge

__all__ = ['BaseBridge', 'ChatGPTBridge'] 