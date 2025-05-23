# Agent Communication Guide

## Overview
This guide explains how to effectively communicate with other agents in the Dream.OS network using various communication channels and protocols.

## Communication Channels

### 1. Direct Messages
```python
from dreamos.core import Message, MessageMode

# Send a direct message
message = Message(
    to_agent="Agent-1",
    content="Requesting data processing assistance",
    mode=MessageMode.COLLAB
)
```

### 2. Broadcast Messages
```python
# Send to all agents
message = Message(
    to_agent="ALL",
    content="System maintenance scheduled",
    mode=MessageMode.SYSTEM
)
```

### 3. Task Assignment
```python
# Assign a task
message = Message(
    to_agent="Agent-3",
    content="Process dataset X",
    mode=MessageMode.TASK
)
```

## Message Modes

### 1. Normal Communication
- `MessageMode.NORMAL`: Standard communication
- Use for: General updates, information sharing

### 2. Task Management
- `MessageMode.TASK`: Task assignment and updates
- Use for: Task distribution, progress updates

### 3. System Operations
- `MessageMode.SYSTEM`: System-level operations
- Use for: Maintenance, updates, alerts

### 4. Collaboration
- `MessageMode.COLLAB`: Inter-agent collaboration
- Use for: Resource sharing, joint operations

### 5. Emergency
- `MessageMode.EMERGENCY`: Critical situations
- Use for: System failures, security alerts

## Best Practices

### 1. Message Structure
```python
# Good message structure
message = Message(
    to_agent="Agent-1",
    content="Requesting assistance with data processing",
    mode=MessageMode.COLLAB,
    metadata={
        "request_type": "data_processing",
        "priority": "high",
        "deadline": "2024-03-20T12:00:00"
    }
)
```

### 2. Response Handling
```python
# Acknowledge receipt
logger.log(
    "Received message from Agent-1",
    category="COLLAB",
    metadata={
        "message_type": "data_request",
        "response_time": "0.5s"
    }
)

# Send response
response = Message(
    to_agent="Agent-1",
    content="Data processing request accepted",
    mode=MessageMode.COLLAB
)
```

### 3. Error Handling
```python
# Handle communication errors
try:
    send_message(message)
except CommunicationError as e:
    logger.log(
        f"Failed to send message: {str(e)}",
        category="ERROR",
        metadata={
            "error_type": "communication",
            "retry_count": 1
        }
    )
```

## Communication Protocols

### 1. Request-Response
```python
# Send request
request = Message(
    to_agent="Agent-1",
    content="Requesting resource access",
    mode=MessageMode.COLLAB
)

# Wait for response
response = await wait_for_response(request.id)
```

### 2. Broadcast-Listen
```python
# Send broadcast
broadcast = Message(
    to_agent="ALL",
    content="System update available",
    mode=MessageMode.SYSTEM
)

# Listen for responses
responses = await collect_responses(broadcast.id)
```

### 3. Task Distribution
```python
# Distribute task
task = Message(
    to_agent="ALL",
    content="Process data batch",
    mode=MessageMode.TASK,
    metadata={
        "batch_id": "BATCH-123",
        "priority": "high"
    }
)

# Monitor progress
progress = await monitor_task_progress(task.id)
```

## Security Considerations

### 1. Message Validation
- Verify sender identity
- Validate message format
- Check message integrity

### 2. Access Control
- Respect agent permissions
- Follow security protocols
- Report suspicious activity

### 3. Data Protection
- Encrypt sensitive data
- Use secure channels
- Maintain audit logs

## Troubleshooting

### Common Issues

1. **Message Not Delivered**
   - Check agent status
   - Verify message format
   - Confirm channel availability

2. **Response Timeout**
   - Check agent responsiveness
   - Verify message priority
   - Consider retry strategy

3. **Communication Errors**
   - Check network status
   - Verify agent permissions
   - Review error logs

## Support

If you encounter communication issues:
1. Check the agent status
2. Review the communication logs
3. Contact the system administrator

Remember: Effective communication is essential for successful agent collaboration. Always be clear, concise, and responsive. 