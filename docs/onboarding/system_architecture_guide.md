# System Architecture Guide

## Overview

This guide provides a detailed overview of the Dream.OS system architecture, including core components, communication flows, and integration points.

## System Components

### Core Components

1. **Agent System**
   - Agent Base
   - Agent Captain
   - Message Processor
   - Cell Phone Interface

2. **Communication System**
   - Message Queue
   - Rate Limiter
   - Priority Handler
   - Broadcast Manager

3. **Logging System**
   - DevLog Manager
   - System Logger
   - Error Handler
   - Performance Monitor

4. **File System**
   - Agent Directories
   - Message Storage
   - Log Files
   - Configuration Files

## Component Details

### Agent System

#### Agent Base
```python
class AgentBase:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.status = "initialized"
        self.messages = []
        self.devlog = None
```

#### Agent Captain
```python
class AgentCaptain:
    def __init__(self):
        self.agents = {}
        self.message_queue = MessageQueue()
        self.rate_limiter = RateLimiter()
```

#### Message Processor
```python
class MessageProcessor:
    def __init__(self):
        self.priority_handler = PriorityHandler()
        self.broadcast_manager = BroadcastManager()
```

#### Cell Phone Interface
```python
class CellPhone:
    def __init__(self):
        self.message_queue = MessageQueue()
        self.rate_limiter = RateLimiter()
```

### Communication System

#### Message Queue
```python
class MessageQueue:
    def __init__(self):
        self.queue = []
        self.priority_levels = 6  # 0-5
```

#### Rate Limiter
```python
class RateLimiter:
    def __init__(self):
        self.limits = {
            "NORMAL": 10,  # messages per minute
            "URGENT": 20,
            "BROADCAST": 5,
            "SYSTEM": 100
        }
```

#### Priority Handler
```python
class PriorityHandler:
    def __init__(self):
        self.priorities = {
            0: "NORMAL",
            1: "LOW",
            2: "MEDIUM",
            3: "HIGH",
            4: "VERY_HIGH",
            5: "CRITICAL"
        }
```

#### Broadcast Manager
```python
class BroadcastManager:
    def __init__(self):
        self.broadcast_groups = {}
        self.message_history = []
```

### Logging System

#### DevLog Manager
```python
class DevLogManager:
    def __init__(self):
        self.logs = {}
        self.max_log_size = 1000  # lines
```

#### System Logger
```python
class SystemLogger:
    def __init__(self):
        self.log_levels = {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 2,
            "ERROR": 3,
            "CRITICAL": 4
        }
```

#### Error Handler
```python
class ErrorHandler:
    def __init__(self):
        self.error_types = {
            "VALIDATION": 1,
            "PERMISSION": 2,
            "SYSTEM": 3,
            "NETWORK": 4
        }
```

#### Performance Monitor
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            "message_count": 0,
            "error_count": 0,
            "response_time": []
        }
```

## System Flow

### Message Flow
1. **Message Creation**
   ```mermaid
   graph LR
   A[Agent] --> B[Cell Phone]
   B --> C[Message Queue]
   C --> D[Message Processor]
   D --> E[Recipient Agent]
   ```

2. **Priority Handling**
   ```mermaid
   graph LR
   A[Message] --> B{Priority Check}
   B -->|High| C[Urgent Queue]
   B -->|Normal| D[Standard Queue]
   C --> E[Processing]
   D --> E
   ```

3. **Broadcast Flow**
   ```mermaid
   graph LR
   A[Broadcast] --> B[Broadcast Manager]
   B --> C[Group Filter]
   C --> D[Recipients]
   D --> E[Message Queue]
   ```

### System Integration

#### Agent Integration
```python
class AgentIntegration:
    def __init__(self):
        self.agent_base = AgentBase
        self.message_processor = MessageProcessor
        self.devlog_manager = DevLogManager
```

#### Message Integration
```python
class MessageIntegration:
    def __init__(self):
        self.cell_phone = CellPhone
        self.priority_handler = PriorityHandler
        self.broadcast_manager = BroadcastManager
```

#### Logging Integration
```python
class LoggingIntegration:
    def __init__(self):
        self.system_logger = SystemLogger
        self.error_handler = ErrorHandler
        self.performance_monitor = PerformanceMonitor
```

## File System Structure

```
dreamos/
├── core/
│   ├── __init__.py
│   ├── agent_base.py
│   ├── agent_captain.py
│   ├── agent_devlog.py
│   ├── cell_phone.py
│   ├── cell_phone_cli.py
│   ├── cursor_controller.py
│   ├── message_processor.py
│   └── rate_limiter.py
├── agents/
│   ├── __init__.py
│   ├── agent_1/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── devlog.txt
│   └── agent_2/
│       ├── __init__.py
│       ├── agent.py
│       └── devlog.txt
├── logs/
│   ├── system.log
│   └── error.log
└── config/
    ├── agents.json
    └── system.json
```

## Configuration

### Agent Configuration
```json
{
    "agent_id": "Agent-1",
    "name": "Example Agent",
    "type": "standard",
    "permissions": ["read", "write"],
    "rate_limit": 10,
    "priority_level": 3
}
```

### System Configuration
```json
{
    "max_agents": 100,
    "message_timeout": 300,
    "log_retention": 30,
    "rate_limits": {
        "NORMAL": 10,
        "URGENT": 20,
        "BROADCAST": 5,
        "SYSTEM": 100
    }
}
```

## Security

### Access Control
```python
class AccessControl:
    def __init__(self):
        self.permissions = {
            "read": ["agent", "message", "log"],
            "write": ["message", "log"],
            "admin": ["system", "config"]
        }
```

### Message Security
```python
class MessageSecurity:
    def __init__(self):
        self.validation_rules = {
            "max_length": 1000,
            "allowed_chars": "a-zA-Z0-9",
            "required_fields": ["to", "content"]
        }
```

## Performance

### Monitoring
```python
class SystemMonitor:
    def __init__(self):
        self.metrics = {
            "cpu_usage": [],
            "memory_usage": [],
            "message_rate": [],
            "error_rate": []
        }
```

### Optimization
```python
class SystemOptimizer:
    def __init__(self):
        self.optimization_rules = {
            "message_batch_size": 100,
            "log_rotation_size": 1000,
            "cache_size": 1000
        }
```

## Error Handling

### Error Types
```python
class ErrorTypes:
    VALIDATION = 1
    PERMISSION = 2
    SYSTEM = 3
    NETWORK = 4
```

### Error Recovery
```python
class ErrorRecovery:
    def __init__(self):
        self.recovery_strategies = {
            "message_retry": 3,
            "system_restart": True,
            "log_backup": True
        }
```

## Additional Resources

- [Agent Communication Guide](./agent_communication_guide.md)
- [Agent Development Guide](./agent_development_guide.md)
- [CLI Usage Guide](./cli_usage_guide.md) 