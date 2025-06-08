# ChatGPT Bridge Integration

## Overview

The ChatGPT Bridge Integration provides a robust interface for agents to communicate with ChatGPT through the bridge system. It handles message routing, response tracking, and health monitoring.

## Core Components

### BridgeIntegration

The main interface for agents to interact with ChatGPT.

#### Key Methods

- `start()`: Initializes the bridge, starts health monitoring, and begins processing requests
- `stop()`: Graceful shutdown of the bridge and cleanup of resources
- `send_to_agent(agent_id, message, msg_type)`: Sends a message to an agent and waits for response
- `get_health_status()`: Returns current health metrics and status
- `get_agent_responses(agent_id)`: Retrieves tracked responses for an agent

#### Message Types

The bridge supports various message types for different use cases:

- `default`: Standard message
- `plan_request`: Request for task planning
- `debug_trace`: Debug information
- `task_summary`: Task completion summary

## Integration with Core Systems

The bridge integrates with several core systems:

- `ChatGPTBridge`: Core bridge functionality
- `RequestQueue`: Message queuing system
- `AgentResponseTracker`: Response tracking
- `BridgeHealthMonitor`: Health monitoring

## Usage Example

```python
from dreamos.core.messaging.bridge_integration import BridgeIntegration

# Initialize bridge
bridge = BridgeIntegration()

# Start bridge
await bridge.start()

# Send message to ChatGPT
response = await bridge.send_to_agent(
    agent_id="agent-1",
    message="Analyze this code and suggest improvements",
    msg_type="plan_request"
)

# Get health status
status = bridge.get_health_status()
print(f"Bridge health: {status}")

# Stop bridge
await bridge.stop()
```

## Configuration

The bridge is configured through `config/chatgpt_bridge.yaml`:

```yaml
# Bridge settings
window_title: "Cursor"
page_load_wait: 30.0
response_wait: 10.0
paste_delay: 0.5

# Retry settings
max_retries: 5
backoff_factor: 2.0

# Health monitoring
health_check_interval: 30.0
session_timeout: 3600.0
```

## Error Handling

The bridge includes robust error handling:

- Automatic retries with exponential backoff
- Health monitoring and status reporting
- Response tracking and metrics
- Graceful error recovery

## Metrics

The bridge tracks various metrics:

- Total requests
- Successful/failed requests
- Average response time
- Last error
- Agent-specific metrics

## Best Practices

1. Always use the `msg_type` parameter to categorize messages
2. Monitor health status regularly
3. Handle responses asynchronously
4. Use retry logic for critical operations
5. Clean up resources with `stop()`

## Troubleshooting

Common issues and solutions:

1. **Bridge not responding**
   - Check health status
   - Verify configuration
   - Check browser state

2. **Slow responses**
   - Monitor metrics
   - Check queue status
   - Verify network connection

3. **Message failures**
   - Check message format
   - Verify agent ID
   - Check response tracking 