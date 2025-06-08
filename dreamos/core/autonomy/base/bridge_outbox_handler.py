"""
Bridge Outbox Handler Shim
------------------------
Maintains backward compatibility by re-exporting the handler from its new location.
"""

from ..handlers.bridge_outbox_handler import BridgeOutboxHandler

__all__ = ['BridgeOutboxHandler'] 