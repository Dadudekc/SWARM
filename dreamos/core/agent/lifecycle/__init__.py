"""Compatibility package for legacy agent lifecycle imports.

This lightweight stub exports `AgentOnboarder` and `AgentManager` placeholders
so that historical import paths continue to resolve.
"""
from __future__ import annotations

from .agent_onboarder import AgentOnboarder, AgentManager  # noqa: F401

__all__: list[str] = [
    "AgentOnboarder",
    "AgentManager",
]

class AgentResumeManager:  # noqa: D401
    """Placeholder for legacy resume manager."""

    def __init__(self, *args, **kwargs):
        pass

__all__.append("AgentResumeManager") 