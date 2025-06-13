# Agent System

The Agent System is responsible for managing agent lifecycle, state, and control within Dream.OS.

## Directory Structure

```
agent/
├── control/          # Agent control and management
├── lifecycle/        # Agent lifecycle management
└── state/           # Agent state management
```

## Components

### Control
- Agent initialization and shutdown
- Agent coordination and communication
- Task scheduling and execution
- Resource management

### Lifecycle
- Agent creation and destruction
- State transitions
- Recovery and error handling
- Health monitoring

### State
- State persistence
- State transitions
- State validation
- State recovery

## Key Features

1. **Agent Management**
   - Agent creation and initialization
   - Agent shutdown and cleanup
   - Agent state tracking
   - Resource allocation

2. **Lifecycle Management**
   - State transitions
   - Error recovery
   - Health monitoring
   - Resource cleanup

3. **State Management**
   - State persistence
   - State validation
   - State recovery
   - State synchronization

## Usage

```python
from dreamos.core.agent.control import AgentController
from dreamos.core.agent.lifecycle import AgentLifecycle
from dreamos.core.agent.state import AgentState

# Initialize agent
controller = AgentController()
lifecycle = AgentLifecycle()
state = AgentState()

# Start agent
controller.start_agent(agent_id="agent1")

# Monitor state
state.get_current_state(agent_id="agent1")

# Handle lifecycle
lifecycle.transition_state(agent_id="agent1", new_state="running")
```

## Configuration

Agent configuration is managed through the `config/agent/` directory:

- `agent_config.yaml`: Main agent configuration
- `agent_roles.json`: Agent role definitions
- `agent_regions.json`: Agent region assignments

## Testing

Run agent system tests:

```bash
pytest tests/unit/agent/
pytest tests/integration/agent/
```

## Contributing

1. Follow the code style guide
2. Add tests for new features
3. Update documentation
4. Submit pull requests 