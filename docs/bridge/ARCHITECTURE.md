# Bridge Architecture

## Overview

The ChatGPT Bridge Integration provides a robust interface for agents to communicate with ChatGPT through the bridge system. It handles message routing, response tracking, and health monitoring.

## 1. Directory Structure

```
dreamos/
├── core/
│   └── bridge/                    # All bridge-related code
│       ├── __init__.py
│       ├── base/                  # Base classes and interfaces
│       │   ├── __init__.py
│       │   ├── bridge.py         # Base bridge interface
│       │   ├── handler.py        # Base handler interface
│       │   └── processor.py      # Base processor interface
│       ├── chatgpt/              # ChatGPT integration
│       │   ├── __init__.py
│       │   ├── bridge.py         # ChatGPT bridge implementation
│       │   ├── prompt.py         # Prompt management
│       │   └── templates/        # Jinja2 templates
│       ├── handlers/             # Bridge handlers
│       │   ├── __init__.py
│       │   ├── outbox.py         # Outbox handler
│       │   └── inbox.py          # Inbox handler
│       ├── processors/           # Response processors
│       │   ├── __init__.py
│       │   ├── base.py          # Base processor
│       │   ├── core.py          # Core processor
│       │   └── bridge.py        # Bridge processor
│       └── monitoring/           # Monitoring and metrics
│           ├── __init__.py
│           ├── metrics.py        # Metrics collection
│           └── health.py         # Health monitoring
└── bridge/                       # Bridge CLI and utilities
    ├── __init__.py
    ├── cli.py                    # Command-line interface
    └── utils.py                  # Utility functions
```

## 2. Core Components

### 2.1 BridgeIntegration

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

### 2.2 Component Consolidation

#### Bridge Implementation
- Consolidate all `ChatGPTBridge` implementations into `core/bridge/chatgpt/bridge.py`
- Single source of truth for bridge functionality
- Clear interface through base classes

#### Response Loop
- Single `ResponseLoop` implementation in `core/bridge/base/loop.py`
- Configurable through processor and handler injection
- No duplicate implementations

#### Handlers
- Unified `BridgeHandler` in `core/bridge/handlers/base.py`
- Specialized handlers inherit from base
- Clear separation of concerns

#### Processors
- Single processor hierarchy in `core/bridge/processors/`
- Factory pattern for creating processors
- No duplicate implementations

## 3. Integration with Core Systems

The bridge integrates with several core systems:

- `ChatGPTBridge`: Core bridge functionality
- `RequestQueue`: Message queuing system
- `AgentResponseTracker`: Response tracking
- `BridgeHealthMonitor`: Health monitoring

## 4. Configuration

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

## 5. Error Handling and Monitoring

### 5.1 Error Handling
- Automatic retries with exponential backoff
- Health monitoring and status reporting
- Response tracking and metrics
- Graceful error recovery

### 5.2 Metrics
The bridge tracks various metrics:
- Total requests
- Successful/failed requests
- Average response time
- Last error
- Agent-specific metrics

## 6. Best Practices

1. Always use the `msg_type` parameter to categorize messages
2. Monitor health status regularly
3. Handle responses asynchronously
4. Use retry logic for critical operations
5. Clean up resources with `stop()`

## 7. Troubleshooting

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

## 8. Benefits

1. **Reduced Duplication**
   - Single implementation of each component
   - Clear inheritance hierarchy
   - Shared utilities

2. **Better Organization**
   - Logical component grouping
   - Clear dependencies
   - Easy to find code

3. **Improved Maintainability**
   - Centralized changes
   - Consistent patterns
   - Better testing

4. **Enhanced Extensibility**
   - Clear extension points
   - Plugin architecture
   - Version control 