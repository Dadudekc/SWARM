# Bridge System

The bridge system provides a unified interface for communication between agents and external services (e.g. ChatGPT). It handles message processing, response validation, and monitoring.

## Architecture

The bridge system consists of the following components:

### Base Components

- `BaseBridge`: Abstract base class for bridge implementations
- `BaseHandler`: Abstract base class for file handlers
- `BaseProcessor`: Abstract base class for message/response processors

### Bridge Implementation

- `ChatGPTBridge`: Implementation of the bridge interface for ChatGPT
- `PromptManager`: Manages prompt generation and templates

### Handlers

- `BridgeOutboxHandler`: Handles outgoing messages
- `BridgeInboxHandler`: Handles incoming responses

### Processors

- `BridgeMessageProcessor`: Processes outgoing messages
- `BridgeResponseProcessor`: Processes incoming responses

### Monitoring

- `BridgeMetrics`: Collects and reports metrics
- `BridgeHealth`: Monitors system health

### Daemon

- `BridgeResponseLoopDaemon`: Main daemon process that coordinates all components

## Configuration

The bridge system is configured via `config.json`. Example configuration:

```json
{
    "paths": {
        "base": "data",
        "archive": "data/archive",
        "failed": "data/failed"
    },
    "bridge": {
        "api_key": "YOUR_API_KEY",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30
    },
    "handlers": {
        "outbox": {
            "file_pattern": "*.json",
            "poll_interval": 1
        },
        "inbox": {
            "file_pattern": "*.json",
            "poll_interval": 1
        }
    },
    "processors": {
        "message": {
            "validate": true,
            "add_metadata": true
        },
        "response": {
            "validate": true,
            "add_metadata": true
        }
    },
    "monitoring": {
        "metrics": {
            "enabled": true,
            "log_interval": 60
        },
        "health": {
            "enabled": true,
            "check_interval": 60,
            "max_failures": 3
        }
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "data/logs/bridge.log"
    }
}
```

## Usage

### Starting the Daemon

```python
from dreamos.core.bridge.daemon import BridgeResponseLoopDaemon

# Create daemon
daemon = BridgeResponseLoopDaemon(config_path="config.json")

# Start daemon
await daemon.start()
```

### Sending Messages

1. Create a message file in the outbox directory:

```json
{
    "content": "Hello, world!",
    "metadata": {
        "type": "greeting",
        "timestamp": "2024-01-01T00:00:00Z"
    }
}
```

2. The daemon will process the message and send it to ChatGPT.

3. The response will be written to the inbox directory.

### Monitoring

The daemon provides metrics and health monitoring:

- Metrics are logged every 60 seconds
- Health checks are performed every 60 seconds
- Failed messages are moved to the failed directory
- Successful messages are archived

## Development

### Adding a New Bridge

1. Create a new bridge class that inherits from `BaseBridge`
2. Implement the required methods
3. Update the daemon to use the new bridge

### Adding a New Handler

1. Create a new handler class that inherits from `BaseHandler`
2. Implement the required methods
3. Update the daemon to use the new handler

### Adding a New Processor

1. Create a new processor class that inherits from `BaseProcessor`
2. Implement the required methods
3. Update the daemon to use the new processor

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

## License

MIT 