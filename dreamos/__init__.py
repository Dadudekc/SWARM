# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

import os

if not os.environ.get("SWARM_SKIP_BRIDGE"):
    from . import bridge
    __all__ = ['bridge']
else:
    __all__ = []
