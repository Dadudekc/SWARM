"""Schema definitions for the resumer system."""

from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field

class TaskData(BaseModel):
    """Schema for task data payload."""
    id: str = Field(..., description="Unique task identifier")
    type: str = Field(..., description="Task type")
    status: str = Field(..., description="Task status")
    created_at: str = Field(..., description="Task creation timestamp")
    updated_at: str = Field(..., description="Task last update timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Task data payload")

class AgentState(BaseModel):
    """Schema for agent state."""
    agent_id: str = Field(..., description="Agent identifier")
    status: str = Field(..., description="Agent status")
    cycle_count: int = Field(..., description="Number of cycles completed")
    debug_mode: bool = Field(default=False, description="Debug mode flag")
    last_updated: str = Field(..., description="Last state update timestamp")

def create_default_state(agent_id: str) -> AgentState:
    """Create a default state object."""
    return AgentState(
        agent_id=agent_id,
        status="idle",
        cycle_count=0,
        debug_mode=False,
        last_updated=datetime.now().isoformat()
    )
