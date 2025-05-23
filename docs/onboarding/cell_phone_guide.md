# Cell Phone System Guide

## Overview

The Cell Phone System is Dream.OS's primary messaging infrastructure, enabling agents to communicate with each other through a robust, priority-based messaging system. It supports various message modes, rate limiting, and concurrent message processing.

## Core Concepts

### Message Priorities
- **Level 0**: Critical system messages
- **Level 1**: High-priority agent communications
- **Level 2**: Standard agent messages
- **Level 3**: Low-priority notifications
- **Level 4**: Background tasks
- **Level 5**: Debug/informational messages

### Message Modes
- **NORMAL**: Standard message delivery
- **RESUME**: Resume agent operation
- **PAUSE**: Pause agent operation
- **STOP**: Stop agent operation
- **DEBUG**: Debug mode messages

## Using the Cell Phone System

### CLI Interface

1. **Basic Message Sending**
   ```bash
   # Send a welcome message
   python -m dreamos.core.cell_phone_cli --welcome --to Agent-1

   # Send a custom message
   python -m dreamos.core.cell_phone_cli --to Agent-1 --message "Hello" --priority 2

   # Send with specific mode
   python -m dreamos.core.cell_phone_cli --to Agent-1 --message "Resume" --mode RESUME
   ```

2. **Message Options**
   ```bash
   --to AGENT_ID      # Target agent ID
   --message TEXT     # Message content
   --priority LEVEL   # Priority (0-5)
   --mode MODE        # Message mode
   --welcome          # Send welcome message
   ```

### Programmatic Usage

1. **Sending Messages**
   ```python
   from dreamos.core.cell_phone import CellPhone

   # Initialize cell phone
   cell_phone = CellPhone()

   # Send message
   cell_phone.send_message(
       to="Agent-1",
       message="Hello",
       priority=2,
       mode="NORMAL"
   )
   ```

2. **Message Handling**
   ```python
   # Register message handler
   @cell_phone.on_message
   def handle_message(message):
       print(f"Received: {message.content}")
   ```

## Message Processing

### Queue Management
- Messages are queued by priority
- Higher priority messages are processed first
- Rate limiting prevents message flooding
- Concurrent processing for multiple agents

### Message States
1. **Queued**: Message is in the processing queue
2. **Processing**: Message is being handled
3. **Delivered**: Message reached the recipient
4. **Failed**: Message delivery failed

## Best Practices

### Message Sending
1. **Choose Appropriate Priority**
   - Use Level 0 for critical system messages
   - Use Level 2 for standard communication
   - Avoid overusing high priorities

2. **Message Content**
   - Keep messages concise
   - Use clear, descriptive content
   - Include necessary context

3. **Error Handling**
   - Implement retry logic
   - Handle delivery failures
   - Log message status

### Performance Considerations
1. **Rate Limiting**
   - Respect rate limits
   - Implement backoff strategies
   - Monitor message queues

2. **Resource Management**
   - Clean up old messages
   - Monitor queue sizes
   - Handle message timeouts

## Troubleshooting

### Common Issues

1. **Message Not Delivered**
   - Check agent status
   - Verify message format
   - Check rate limits
   - Review error logs

2. **Queue Backlog**
   - Monitor queue sizes
   - Check processing speed
   - Review rate limits
   - Optimize message handling

3. **Performance Issues**
   - Check system resources
   - Review message patterns
   - Optimize queue processing
   - Monitor rate limits

## Advanced Features

### Message History
```python
# Get message history
history = cell_phone.get_message_history(agent_id="Agent-1")

# Filter history
filtered = cell_phone.get_message_history(
    agent_id="Agent-1",
    priority=2,
    mode="NORMAL"
)
```

### Status Tracking
```python
# Get agent status
status = cell_phone.get_agent_status(agent_id="Agent-1")

# Monitor message queue
queue_status = cell_phone.get_queue_status()
```

### Custom Handlers
```python
# Register custom handler
@cell_phone.on_message
def custom_handler(message):
    if message.mode == "RESUME":
        handle_resume(message)
    elif message.mode == "PAUSE":
        handle_pause(message)
```

## Related Documentation
- [System Architecture](system_architecture.md)
- [Development Setup](development_setup.md)
- [Testing Guide](testing_guide.md) 