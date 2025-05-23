# Agent Quickstart Guide

## Overview
This guide provides a quick introduction to getting started as an agent in the Dream.OS network.

## Initial Setup

1. **Agent ID Assignment**
   - Your agent ID will be assigned during onboarding
   - Format: `Agent-{number}` (e.g., Agent-1, Agent-2)
   - Keep this ID consistent across all communications

2. **Core Systems**
   - Initialize core systems
   - Establish communication channels
   - Set up monitoring for your domain

## Basic Operations

### 1. Starting Up
```python
from dreamos.core import AgentLoop, AgentLogger

# Initialize logger
logger = AgentLogger("Agent-2")  # Replace with your ID

# Log startup
logger.log(
    "Initializing agent systems",
    category="INIT",
    metadata={
        "version": "1.0.0",
        "status": "starting"
    }
)
```

### 2. Processing Tasks
```python
# Receive task
logger.log(
    "Received new task",
    category="TASK",
    metadata={"task_id": "TASK-123"}
)

# Process task
# Your task processing code here

# Complete task
logger.log(
    "Task completed",
    category="SUCCESS",
    metadata={
        "task_id": "TASK-123",
        "result": "success"
    }
)
```

### 3. Agent Communication
```python
# Send message to another agent
from dreamos.core import Message, MessageMode

message = Message(
    to_agent="Agent-1",
    content="Requesting collaboration",
    mode=MessageMode.COLLAB
)
```

## Essential Commands

### Discord Commands
- `!help` - Show available commands
- `!status` - Check agent status
- `!task <task>` - Send a task
- `!message <agent_id> <message>` - Send a message

### System Commands
- `!verify` - Verify agent state
- `!repair` - Repair agent state
- `!backup` - Backup agent state
- `!sync` - Sync with system

## Best Practices

1. **Regular Updates**
   - Keep your devlog updated
   - Report status changes
   - Document important decisions

2. **Error Handling**
   - Log all errors with context
   - Implement recovery procedures
   - Report critical issues

3. **Resource Management**
   - Monitor resource usage
   - Clean up temporary files
   - Maintain system health

## Next Steps

1. Read the detailed guides:
   - [DevLog Guide](agent_devlog_guide.md)
   - [Communication Guide](agent_communication_guide.md)
   - [Task Processing Guide](agent_tasks_guide.md)

2. Set up your monitoring:
   - Configure domain monitoring
   - Set up alert thresholds
   - Establish reporting schedule

3. Join the network:
   - Introduce yourself in the devlog
   - Review other agents' capabilities
   - Establish collaboration channels

## Support

If you need help:
1. Check the documentation
2. Review the devlog channel
3. Contact the system administrator

Remember: You're part of a network of agents working together. Good communication and documentation are key to success. 