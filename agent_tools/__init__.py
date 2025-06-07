# AUTO-GENERATED __init__.py
# DO NOT EDIT MANUALLY - changes may be overwritten

import os

if not os.environ.get("SWARM_SKIP_BRIDGE"):
    from . import activate_test_debug
    _activate_debug = ['activate_test_debug']
else:
    _activate_debug = []
if not os.environ.get("SWARM_SKIP_BRIDGE"):
    from . import agent_restart
    _restart = ['agent_restart']
else:
    _restart = []
from . import agent_resumer
from . import captain_prompt
from . import cursor_chatgpt_bridge
from . import setup

__all__ = [
    *_activate_debug,
    *_restart,
    'agent_resumer',
    'captain_prompt',
    'cursor_chatgpt_bridge',
    'setup',
]
