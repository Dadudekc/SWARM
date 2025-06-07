"""
Base State Manager
----------------
Provides unified state management functionality for all agents.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from enum import Enum, auto

logger = logging.getLogger(__name__)

class AgentStateType(Enum):
    """Enumeration of possible agent states."""
    IDLE = auto()
    PROCESSING = auto()
    RESUMING = auto()
    ERROR = auto()
    ARCHIVING = auto()
    NOTIFYING = auto()

class StateTransitionError(Exception):
    """Raised when a state transition is invalid."""
    pass

class StateCorruptionError(Exception):
    """Raised when state data is corrupted."""
    pass

class BaseStateManager:
    """Base class for unified state management."""
    
    # Default timeouts
    IDLE_TIMEOUT = timedelta(minutes=5)
    PROCESSING_TIMEOUT = timedelta(minutes=30)
    ERROR_RETRY_TIMEOUT = timedelta(minutes=1)
    
    # Recovery settings
    MAX_RECOVERY_ATTEMPTS = 3
    RECOVERY_BACKOFF_BASE = 2  # seconds
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the state manager.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.agents: Dict[str, Dict] = {}  # agent_id -> state_data
        self._recovery_attempts: Dict[str, int] = {}  # agent_id -> attempt count
        self._state_locks: Dict[str, asyncio.Lock] = {}  # agent_id -> lock
        self._setup_metrics()
        self._setup_recovery()
    
    def _setup_metrics(self) -> None:
        """Set up monitoring metrics."""
        from prometheus_client import Counter, Histogram, Gauge
        
        self.state_transitions = Counter(
            'agent_state_transitions_total',
            'Total number of state transitions',
            ['agent_id', 'from_state', 'to_state']
        )
        
        self.state_duration = Histogram(
            'agent_state_duration_seconds',
            'Time spent in each state',
            ['agent_id', 'state']
        )
        
        self.error_count = Counter(
            'agent_state_errors_total',
            'Total number of state errors',
            ['agent_id', 'error_type']
        )
        
        self.active_agents = Gauge(
            'active_agents',
            'Number of currently active agents',
            ['state']
        )
        
        self.recovery_attempts = Counter(
            'agent_state_recovery_attempts_total',
            'Total number of recovery attempts',
            ['agent_id', 'success']
        )
        
        self.state_backups = Counter(
            'agent_state_backups_total',
            'Total number of state backups',
            ['agent_id', 'success']
        )
    
    def _setup_recovery(self) -> None:
        """Set up recovery infrastructure."""
        self.backup_dir = Path(self.config.get("backup_dir", "state_backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create recovery event queue
        self.recovery_events = asyncio.Queue()
    
    async def _backup_state(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Backup current state to disk.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            if agent_id not in self.agents:
                return False, f"No state to backup for agent {agent_id}"
            
            backup_file = self.backup_dir / f"{agent_id}_state.json"
            backup_data = {
                "agent_id": agent_id,
                "state": self.agents[agent_id]["state"].name,
                "last_update": self.agents[agent_id]["last_update"].isoformat(),
                "history": self.agents[agent_id]["history"],
                "metadata": self.agents[agent_id]["metadata"],
                "backup_time": datetime.utcnow().isoformat()
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            self.state_backups.labels(
                agent_id=agent_id,
                success=True
            ).inc()
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error backing up state for agent {agent_id}: {e}"
            logger.error(error_msg)
            self.state_backups.labels(
                agent_id=agent_id,
                success=False
            ).inc()
            return False, error_msg
    
    async def _load_backup(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Load state from backup.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            backup_file = self.backup_dir / f"{agent_id}_state.json"
            if not backup_file.exists():
                return False, f"No backup found for agent {agent_id}"
            
            with open(backup_file) as f:
                backup_data = json.load(f)
            
            # Validate backup data
            if not self._validate_backup(backup_data):
                raise StateCorruptionError(f"Invalid backup data for agent {agent_id}")
            
            # Restore state
            self.agents[agent_id] = {
                "state": AgentStateType[backup_data["state"]],
                "last_update": datetime.fromisoformat(backup_data["last_update"]),
                "history": backup_data["history"],
                "metadata": backup_data["metadata"]
            }
            
            return True, None
            
        except Exception as e:
            error_msg = f"Error loading backup for agent {agent_id}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    def _validate_backup(self, backup_data: Dict) -> bool:
        """Validate backup data.
        
        Args:
            backup_data: Backup data to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = {"agent_id", "state", "last_update", "history", "metadata", "backup_time"}
        if not all(field in backup_data for field in required_fields):
            return False
        
        try:
            # Validate state
            AgentStateType[backup_data["state"]]
            
            # Validate timestamps
            datetime.fromisoformat(backup_data["last_update"])
            datetime.fromisoformat(backup_data["backup_time"])
            
            # Validate history
            if not isinstance(backup_data["history"], list):
                return False
            
            # Validate metadata
            if not isinstance(backup_data["metadata"], dict):
                return False
            
            return True
            
        except (ValueError, KeyError):
            return False
    
    async def _get_state_lock(self, agent_id: str) -> asyncio.Lock:
        """Get or create a lock for an agent's state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Lock for the agent's state
        """
        if agent_id not in self._state_locks:
            self._state_locks[agent_id] = asyncio.Lock()
        return self._state_locks[agent_id]
    
    async def update_state(self, agent_id: str, new_state: AgentStateType, metadata: Optional[Dict] = None) -> Tuple[bool, Optional[str]]:
        """Update an agent's state with locking and backup.
        
        Args:
            agent_id: Agent identifier
            new_state: New state
            metadata: Optional metadata about the state change
            
        Returns:
            Tuple of (success, error_message)
        """
        async with await self._get_state_lock(agent_id):
            try:
                current_state = self.get_state(agent_id)
                if current_state and not self._validate_transition(agent_id, current_state, new_state):
                    raise StateTransitionError(f"Invalid transition from {current_state} to {new_state}")
                
                # Record state transition
                if current_state:
                    self.state_transitions.labels(
                        agent_id=agent_id,
                        from_state=current_state.name,
                        to_state=new_state.name
                    ).inc()
                    
                    # Record duration in previous state
                    duration = datetime.utcnow() - self.agents[agent_id]["last_update"]
                    self.state_duration.labels(
                        agent_id=agent_id,
                        state=current_state.name
                    ).observe(duration.total_seconds())
                
                # Update state
                if agent_id not in self.agents:
                    self.agents[agent_id] = {
                        "state": new_state,
                        "last_update": datetime.utcnow(),
                        "history": [],
                        "metadata": metadata or {}
                    }
                else:
                    # Add to history
                    self.agents[agent_id]["history"].append({
                        "state": self.agents[agent_id]["state"],
                        "timestamp": self.agents[agent_id]["last_update"],
                        "metadata": self.agents[agent_id].get("metadata", {})
                    })
                    # Update current state
                    self.agents[agent_id]["state"] = new_state
                    self.agents[agent_id]["last_update"] = datetime.utcnow()
                    self.agents[agent_id]["metadata"] = metadata or {}
                
                # Backup state
                backup_success, backup_error = await self._backup_state(agent_id)
                if not backup_success:
                    logger.warning(f"Failed to backup state: {backup_error}")
                
                # Update metrics
                self._update_metrics(agent_id, new_state)
                
                return True, None
                
            except Exception as e:
                error_msg = f"Error updating state for agent {agent_id}: {e}"
                logger.error(error_msg)
                self.error_count.labels(
                    agent_id=agent_id,
                    error_type=type(e).__name__
                ).inc()
                return False, error_msg
    
    async def recover_from_crash(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Attempt to recover agent state from a crash.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Check recovery attempts
            if agent_id not in self._recovery_attempts:
                self._recovery_attempts[agent_id] = 0
            
            if self._recovery_attempts[agent_id] >= self.MAX_RECOVERY_ATTEMPTS:
                return False, f"Max recovery attempts exceeded for agent {agent_id}"
            
            # Increment recovery attempts
            self._recovery_attempts[agent_id] += 1
            
            # Calculate backoff
            backoff = self.RECOVERY_BACKOFF_BASE ** (self._recovery_attempts[agent_id] - 1)
            await asyncio.sleep(backoff)
            
            # Try to load from backup
            success, error = await self._load_backup(agent_id)
            
            # Record recovery attempt
            self.recovery_attempts.labels(
                agent_id=agent_id,
                success=success
            ).inc()
            
            if success:
                # Reset recovery attempts on success
                self._recovery_attempts[agent_id] = 0
                # Queue recovery event
                await self.recovery_events.put({
                    "agent_id": agent_id,
                    "event_type": "recovery_success",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                # Queue failure event
                await self.recovery_events.put({
                    "agent_id": agent_id,
                    "event_type": "recovery_failure",
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return success, error
            
        except Exception as e:
            error_msg = f"Error during recovery for agent {agent_id}: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def soft_reset(self, agent_id: str) -> Tuple[bool, Optional[str]]:
        """Perform a soft reset of agent state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Tuple of (success, error_message)
        """
        async with await self._get_state_lock(agent_id):
            try:
                if agent_id not in self.agents:
                    return False, f"No state to reset for agent {agent_id}"
                
                # Backup current state
                await self._backup_state(agent_id)
                
                # Reset to IDLE state
                self.agents[agent_id] = {
                    "state": AgentStateType.IDLE,
                    "last_update": datetime.utcnow(),
                    "history": [],
                    "metadata": {}
                }
                
                # Reset recovery attempts
                self._recovery_attempts[agent_id] = 0
                
                # Update metrics
                self._update_metrics(agent_id, AgentStateType.IDLE)
                
                return True, None
                
            except Exception as e:
                error_msg = f"Error during soft reset for agent {agent_id}: {e}"
                logger.error(error_msg)
                return False, error_msg
    
    def get_recovery_events(self) -> asyncio.Queue:
        """Get the recovery events queue.
        
        Returns:
            Queue of recovery events
        """
        return self.recovery_events
    
    def _validate_transition(self, agent_id: str, from_state: AgentStateType, to_state: AgentStateType) -> bool:
        """Validate if a state transition is allowed.
        
        Args:
            agent_id: Agent identifier
            from_state: Current state
            to_state: Target state
            
        Returns:
            True if transition is valid, False otherwise
        """
        # Define valid transitions
        valid_transitions = {
            AgentStateType.IDLE: [AgentStateType.PROCESSING, AgentStateType.ERROR],
            AgentStateType.PROCESSING: [AgentStateType.IDLE, AgentStateType.ERROR, AgentStateType.ARCHIVING],
            AgentStateType.RESUMING: [AgentStateType.PROCESSING, AgentStateType.ERROR],
            AgentStateType.ERROR: [AgentStateType.RESUMING, AgentStateType.IDLE],
            AgentStateType.ARCHIVING: [AgentStateType.IDLE, AgentStateType.ERROR],
            AgentStateType.NOTIFYING: [AgentStateType.IDLE, AgentStateType.ERROR]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    def get_state(self, agent_id: str) -> Optional[AgentStateType]:
        """Get an agent's current state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current state or None if agent not found
        """
        return self.agents.get(agent_id, {}).get("state")
    
    def get_metadata(self, agent_id: str) -> Dict:
        """Get an agent's current metadata.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Current metadata or empty dict if agent not found
        """
        return self.agents.get(agent_id, {}).get("metadata", {})
    
    def get_history(self, agent_id: str) -> List[Dict]:
        """Get an agent's state history.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of state history entries
        """
        return self.agents.get(agent_id, {}).get("history", [])
    
    def is_stuck(self, agent_id: str) -> bool:
        """Check if an agent is stuck in its current state.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent is stuck, False otherwise
        """
        agent_data = self.agents.get(agent_id)
        if not agent_data:
            return False
        
        current_state = agent_data["state"]
        time_in_state = datetime.utcnow() - agent_data["last_update"]
        
        # Check against appropriate timeout
        if current_state == AgentStateType.IDLE:
            return time_in_state > self.IDLE_TIMEOUT
        elif current_state == AgentStateType.PROCESSING:
            return time_in_state > self.PROCESSING_TIMEOUT
        elif current_state == AgentStateType.ERROR:
            return time_in_state > self.ERROR_RETRY_TIMEOUT
        
        return False
    
    def get_stuck_agents(self) -> List[str]:
        """Get list of stuck agents.
        
        Returns:
            List of agent IDs that are stuck
        """
        return [
            agent_id for agent_id in self.agents
            if self.is_stuck(agent_id)
        ]
    
    def _update_metrics(self, agent_id: str, state: AgentStateType) -> None:
        """Update monitoring metrics.
        
        Args:
            agent_id: Agent identifier
            state: Current state
        """
        # Update active agents gauge
        for state_type in AgentStateType:
            count = len([
                a for a, d in self.agents.items()
                if d["state"] == state_type
            ])
            self.active_agents.labels(state=state_type.name).set(count)
    
    def get_stats(self, agent_id: str) -> Dict:
        """Get agent statistics.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary of agent statistics
        """
        agent_data = self.agents.get(agent_id, {})
        return {
            "current_state": agent_data.get("state"),
            "last_update": agent_data.get("last_update"),
            "history": agent_data.get("history", []),
            "metadata": agent_data.get("metadata", {}),
            "is_stuck": self.is_stuck(agent_id) if agent_id in self.agents else False
        }
    
    def get_all_stats(self) -> Dict[str, Dict]:
        """Get statistics for all agents.
        
        Returns:
            Dictionary mapping agent IDs to their statistics
        """
        return {
            agent_id: self.get_stats(agent_id)
            for agent_id in self.agents
        } 