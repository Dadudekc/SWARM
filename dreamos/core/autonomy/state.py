"""State management for autonomous components."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

class State(Enum):
    """Possible states for autonomous components."""
    IDLE = auto()
    PROCESSING = auto()
    ERROR = auto()
    STOPPED = auto()

@dataclass
class StateTransition:
    """Record of a state transition."""
    from_state: State
    to_state: State
    timestamp: datetime
    reason: Optional[str] = None

class StateTransitionError(Exception):
    """Error raised when a state transition is invalid."""
    pass

class StateManager:
    """Manages state transitions for autonomous components.
    
    This class provides functionality to:
    - Track current state
    - Validate state transitions
    - Record transition history
    - Handle state-specific actions
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        State.IDLE: {State.PROCESSING, State.ERROR, State.STOPPED},
        State.PROCESSING: {State.IDLE, State.ERROR, State.STOPPED},
        State.ERROR: {State.IDLE, State.STOPPED},
        State.STOPPED: {State.IDLE}
    }
    
    def __init__(self):
        """Initialize state manager."""
        self._current_state = State.IDLE
        self._transition_history: List[StateTransition] = []
        self._state_lock = asyncio.Lock()
        self._state_handlers: Dict[State, Set[callable]] = {
            state: set() for state in State
        }
    
    @property
    def current_state(self) -> State:
        """Get current state."""
        return self._current_state
    
    @property
    def transition_history(self) -> List[StateTransition]:
        """Get state transition history."""
        return self._transition_history.copy()
    
    async def transition_to(self, new_state: State, reason: Optional[str] = None) -> None:
        """Transition to a new state.
        
        Args:
            new_state: State to transition to
            reason: Optional reason for transition
            
        Raises:
            StateTransitionError: If transition is invalid
        """
        async with self._state_lock:
            if new_state not in self.VALID_TRANSITIONS[self._current_state]:
                raise StateTransitionError(
                    f"Invalid transition from {self._current_state} to {new_state}"
                )
            
            # Record transition
            transition = StateTransition(
                from_state=self._current_state,
                to_state=new_state,
                timestamp=datetime.now(),
                reason=reason
            )
            self._transition_history.append(transition)
            
            # Update state
            old_state = self._current_state
            self._current_state = new_state
            
            # Call state handlers
            for handler in self._state_handlers[new_state]:
                try:
                    await handler(old_state, new_state)
                except Exception as e:
                    logger.error(f"Error in state handler: {e}")
    
    def add_state_handler(self, state: State, handler: callable) -> None:
        """Add a handler for state transitions.
        
        Args:
            state: State to handle
            handler: Async function(state, new_state) to call on transition
        """
        self._state_handlers[state].add(handler)
    
    def remove_state_handler(self, state: State, handler: callable) -> None:
        """Remove a state transition handler.
        
        Args:
            state: State to remove handler from
            handler: Handler to remove
        """
        self._state_handlers[state].discard(handler)
    
    def clear_handlers(self) -> None:
        """Clear all state handlers."""
        for state in State:
            self._state_handlers[state].clear()
    
    def get_transitions_since(self, timestamp: datetime) -> List[StateTransition]:
        """Get transitions since a timestamp.
        
        Args:
            timestamp: Get transitions after this time
            
        Returns:
            List of transitions
        """
        return [
            t for t in self._transition_history
            if t.timestamp > timestamp
        ]
    
    def get_last_transition(self) -> Optional[StateTransition]:
        """Get the most recent state transition.
        
        Returns:
            Last transition or None if no transitions
        """
        return self._transition_history[-1] if self._transition_history else None
    
    def reset(self) -> None:
        """Reset state manager to initial state."""
        self._current_state = State.IDLE
        self._transition_history.clear()
        self.clear_handlers() 
