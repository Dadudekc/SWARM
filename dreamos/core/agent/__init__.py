"""
Dream.OS Agent System

This module provides the core agent functionality for Dream.OS.
It includes agent control, lifecycle management, and state management.
"""

from .control import (
    AgentController,
    AgentControl,
    AgentOperations,
    AgentStatus,
    AgentStatusInfo,
    AgentSelectionDialog,
    AgentCellphone,
    AgentRestarter
)

from .lifecycle import (
    AgentOnboarder,
    AgentManager,
    AgentResumeManager
)

from .state import (
    AgentState,
    AgentStateManager,
    QuantumAgentResumer,
    AgentStateSchema
)

__all__ = [
    # Control
    'AgentController',
    'AgentControl',
    'AgentOperations',
    'AgentStatus',
    'AgentStatusInfo',
    'AgentSelectionDialog',
    'AgentCellphone',
    'AgentRestarter',
    
    # Lifecycle
    'AgentOnboarder',
    'AgentManager',
    'AgentResumeManager',
    
    # State
    'AgentState',
    'AgentStateManager',
    'QuantumAgentResumer',
    'AgentStateSchema'
] 