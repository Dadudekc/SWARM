"""
Shared module containing common functionality used across Dream.OS.

This module provides core shared components including:
- Coordinate management for spatial operations
- Persistent queue for reliable message handling
- Message and response processors
- Base validation framework
"""

from typing import List, Type

from dreamos.core.shared.coordinate_manager import (
    CoordinateManager,
    load_coordinates,
    save_coordinates,
    get_coordinates,
    set_coordinates
)

from dreamos.core.shared.persistent_queue import (
    PersistentQueue,
    load_queue,
    save_queue
)

from dreamos.core.shared.processors import (
    MessageProcessor,
    ResponseProcessor,
    ProcessorFactory,
    ProcessorMode
)

from dreamos.core.shared.validation.base import (
    BaseValidator
)

__all__: List[str] = [
    # Coordinate Manager
    'CoordinateManager',
    'load_coordinates',
    'save_coordinates',
    'get_coordinates',
    'set_coordinates',
    
    # Persistent Queue
    'PersistentQueue',
    'load_queue',
    'save_queue',
    
    # Processors
    'MessageProcessor',
    'ResponseProcessor',
    'ProcessorFactory',
    'ProcessorMode',
    
    # Validation
    'BaseValidator'
]
