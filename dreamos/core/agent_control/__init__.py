"""Agent control package."""

# Delayed imports to avoid circular reference
from .agent_controller import AgentController
from .periodic_restart import AgentManager, AgentResumeManager
from .ui_automation import UIAutomation
from .task_manager import TaskManager
from .devlog_manager import DevLogManager

__all__ = [
    'AgentController',
    'AgentManager',
    'AgentResumeManager',
    'UIAutomation',
    'TaskManager',
    'DevLogManager'
]

def get_main():
    """Get main module contents on demand to avoid circular imports."""
    from . import main
    return main
