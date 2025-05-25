# Agent Control Architecture

## Overview

The agent control system provides a unified interface for managing agent operations through a messaging-based architecture. It separates concerns between UI interaction, business logic, and message delivery while providing robust fallback mechanisms.

## Component Roles

### AgentController
- Primary entry point for agent operations
- Handles menu interactions and UI feedback
- Delegates all operations to AgentOperations
- No direct message handling logic

### AgentOperations
- Core business logic for all agent operations
- Manages message delivery through MessageProcessor
- Implements fallback to CellPhone when needed
- Handles both UI and non-UI operations

### UIAutomation
- Provides visual feedback only
- No business logic or message handling
- Used for clicks, focus, and visual confirmation
- Optional for all operations

## Message Flow

```
Menu Selection
     ↓
AgentController
     ↓
AgentOperations
     ↓
MessageProcessor (Primary)
     ↓
Agent Inbox (inbox.json)
     ↓
CellPhone (Fallback)
```

## Message Types

| Operation | Mode      | Description                    |
|-----------|-----------|--------------------------------|
| Onboard   | ONBOARD   | Initial agent setup           |
| Resume    | RESUME    | Resume agent operations       |
| Verify    | VERIFY    | Check agent status            |
| Repair    | REPAIR    | Fix agent issues              |
| Backup    | BACKUP    | Backup agent data             |
| Restore   | RESTORE   | Restore from backup           |
| Message   | MESSAGE   | General communication         |

## Message Format

All messages are stored in `inbox.json` with the following structure:

```json
{
    "mode": "RESUME",
    "content": "Resuming operations. Please confirm your status and continue with assigned tasks.",
    "timestamp": "2024-03-14T12:00:00Z",
    "metadata": {
        "source": "MessageProcessor",
        "version": "1.0",
        "priority": "normal"
    }
}
```

## Recovery Mechanism

1. Primary: MessageProcessor
   - Writes to inbox.json
   - Validates message format
   - Handles delivery confirmation

2. Fallback: CellPhone
   - Used when MessageProcessor fails
   - Direct message delivery
   - No message validation

## Best Practices

1. Always use AgentOperations for agent interactions
2. Keep UI automation for visual feedback only
3. Handle errors gracefully with fallback options
4. Validate messages before delivery
5. Clean up resources properly

## Testing

- Unit tests for AgentOperations
- Integration tests for Controller → Inbox flow
- Mock dependencies for isolated testing
- Test both success and failure scenarios

### Example Test Output

```python
def test_resume_agent_uses_message_processor(agent_ops):
    """Test that resume_agent uses MessageProcessor."""
    agent_ops.resume_agent("Agent-1")
    agent_ops.message_processor.send_message.assert_called_with(
        "Agent-1", 
        "Resuming operations. Please confirm your status and continue with assigned tasks.",
        "RESUME"
    )
```

## Troubleshooting

### Common Issues

1. **Agent Not Responding**
   - Check `runtime/mailbox/Agent-X/inbox.json` exists and is valid JSON
   - Verify message has both `mode` and `content` fields
   - Check file permissions on mailbox directory

2. **UI Automation Fails**
   - Verify agent coordinates in `coordinates.json`
   - Check if window is in focus
   - Ensure no other UI automation is running

3. **Message Delivery Fails**
   - Check MessageProcessor logs for errors
   - Verify CellPhone fallback is working
   - Check network connectivity if using remote agents

4. **Corrupt Inbox File**
   ```bash
   # Backup corrupt file
   mv runtime/mailbox/Agent-X/inbox.json runtime/mailbox/Agent-X/inbox.json.bak
   
   # Create new inbox
   echo '{"mode": "RESUME", "content": "System reset"}' > runtime/mailbox/Agent-X/inbox.json
   ```

5. **Permission Issues**
   ```bash
   # Fix mailbox permissions
   chmod -R 755 runtime/mailbox
   chown -R $USER:$USER runtime/mailbox
   ```

## Notes

- All inbox.json messages are validated before write
- UI automation is optional for all operations
- Agent IDs must be unique and valid
- Message content is sanitized before delivery
- Concurrent writes are handled gracefully
- Network errors trigger CellPhone fallback
- Disk full errors are caught and reported
- Invalid agent IDs are rejected early 