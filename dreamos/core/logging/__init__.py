# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

import logging

# Configure basic logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Now import the modules
from . import log_config
from . import log_manager
from . import log_writer
from . import agent_logger

__all__ = [
    'agent_logger',
    'log_config',
    'log_manager',
    'log_writer',
]
