"""
Outbox handler for processing outgoing messages in the bridge system.
"""

from dreamos.core.bridge.base import BridgeHandler
from dreamos.core.bridge.monitoring import BridgeMonitor
from dreamos.core.bridge.validation import BridgeValidator
from dreamos.core.utils.logging_utils import get_logger

# ... existing code ... 