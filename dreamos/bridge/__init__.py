"""
ChatGPT Bridge package.

This package provides a bridge service for interacting with ChatGPT through a web browser.
"""

from .core import ChatGPTBridge
from .models import BridgeRequest, BridgeHealth
from .utils import HybridResponseHandler, parse_hybrid_response

__all__ = [
    'ChatGPTBridge',
    'BridgeRequest',
    'BridgeHealth',
    'HybridResponseHandler',
    'parse_hybrid_response'
] 