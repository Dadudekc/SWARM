# Base State Manager

A resilient state management system for Dream.OS agents.

## Features

### 1. State Management
- Thread-safe state updates with asyncio locks
- State transition validation
- State history tracking
- Metadata support

### 2. Resilience Features
- **State Backup & Recovery**
  - Automatic state backup on updates
  - Backup validation and corruption detection
  - Recovery from crashes with exponential backoff
  - Soft reset capability for graceful state reset

- **Concurrency Control**
  - Thread-safe state updates
  - Lock-based synchronization
  - Atomic state transitions

- **Recovery Mechanisms**
  - Configurable recovery attempts
  - Exponential backoff
  - Recovery event queue for monitoring
  - Graceful degradation

### 3. Monitoring & Metrics
- State transition tracking
- Recovery attempt monitoring
- Backup success/failure metrics
- Error tracking with specific types

## Usage

```python
from dreamos.core.autonomy.base.state_manager import BaseStateManager, AgentStateType

# Initialize with configuration
config = {
    "backup_dir": "state_backups",
    "idle_timeout": 300,
    "processing_timeout": 1800,
    "error_retry_timeout": 60
}
state_manager = BaseStateManager(config)

# Update state
success, error = await state_manager.update_state(
    "agent_1",
    AgentStateType.PROCESSING,
    {"task": "example_task"}
)

# Recover from crash
success, error = await state_manager.recover_from_crash("agent_1")

# Soft reset
success, error = await state_manager.soft_reset("agent_1")
```

## Configuration

| Setting | Description | Default |
|---------|-------------|---------|
| `backup_dir` | Directory for state backups | "state_backups" |
| `idle_timeout` | Timeout for IDLE state (seconds) | 300 |
| `processing_timeout` | Timeout for PROCESSING state (seconds) | 1800 |
| `error_retry_timeout` | Timeout for ERROR state (seconds) | 60 |

## Recovery Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `MAX_RECOVERY_ATTEMPTS` | Maximum recovery attempts | 3 |
| `RECOVERY_BACKOFF_BASE` | Base for exponential backoff (seconds) | 2 |

## State Types

- `IDLE`: Initial state, ready for processing
- `PROCESSING`: Currently processing a task
- `RESUMING`: Recovering from a previous state
- `ERROR`: Error state, requires recovery
- `ARCHIVING`: Archiving completed tasks
- `NOTIFYING`: Sending notifications

## Error Handling

The system handles various error conditions:
- Invalid state transitions
- Corrupted backup data
- Recovery failures
- Concurrent access conflicts

## Monitoring

Metrics are exposed via Prometheus:
- `agent_state_transitions_total`
- `agent_state_duration_seconds`
- `agent_state_errors_total`
- `active_agents`
- `agent_state_recovery_attempts_total`
- `agent_state_backups_total`

## Best Practices

1. **State Updates**
   - Always use `update_state` for state changes
   - Include relevant metadata
   - Handle errors appropriately

2. **Recovery**
   - Monitor recovery events
   - Implement appropriate backoff strategies
   - Handle recovery failures gracefully

3. **Backup**
   - Regularly verify backup integrity
   - Monitor backup success rates
   - Implement backup rotation if needed

4. **Concurrency**
   - Use async/await for state operations
   - Handle lock timeouts appropriately
   - Avoid long-running operations while holding locks

## Contributing

When adding new features:
1. Add appropriate tests
2. Update documentation
3. Add relevant metrics
4. Consider recovery implications 