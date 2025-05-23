# CLI Usage Guide

## Overview

This guide covers the command-line interface (CLI) tools available in Dream.OS for managing agents, sending messages, and monitoring system status.

## Basic Commands

### Agent Management

```bash
# List all agents
python -m dreamos.core.agent_captain list

# Get agent status
python -m dreamos.core.agent_captain status Agent-1

# Clear agent messages
python -m dreamos.core.agent_captain clear Agent-1
```

### Message Sending

```bash
# Send a normal message
python -m dreamos.core.cell_phone_cli --to Agent-1 --message "Hello"

# Send a welcome message
python -m dreamos.core.cell_phone_cli --to Agent-1 --welcome

# Send a priority message
python -m dreamos.core.cell_phone_cli --to Agent-1 --message "Urgent!" --priority 5

# Send a broadcast message
python -m dreamos.core.cell_phone_cli --to Agent-1 --message "Alert" --mode BROADCAST
```

### DevLog Management

```bash
# View agent devlog
python -m dreamos.core.agent_devlog view Agent-1

# Clear agent devlog
python -m dreamos.core.agent_devlog clear Agent-1

# Update devlog
python -m dreamos.core.agent_devlog update Agent-1 "New log entry"
```

## Command Reference

### Agent Captain

#### List Agents
```bash
python -m dreamos.core.agent_captain list [--status STATUS]
```
Options:
- `--status`: Filter by agent status (running, stopped, error)

#### Get Agent Status
```bash
python -m dreamos.core.agent_captain status AGENT_ID
```
Arguments:
- `AGENT_ID`: The ID of the agent to check

#### Clear Agent Messages
```bash
python -m dreamos.core.agent_captain clear AGENT_ID
```
Arguments:
- `AGENT_ID`: The ID of the agent to clear messages for

### Cell Phone CLI

#### Send Message
```bash
python -m dreamos.core.cell_phone_cli --to AGENT_ID [options]
```
Required Arguments:
- `--to`: Recipient agent ID

Options:
- `--message`: Message content
- `--welcome`: Send welcome message
- `--priority`: Message priority (0-5)
- `--mode`: Message mode (NORMAL, URGENT, BROADCAST, SYSTEM)

### Agent DevLog

#### View DevLog
```bash
python -m dreamos.core.agent_devlog view AGENT_ID [--lines N]
```
Arguments:
- `AGENT_ID`: The ID of the agent
- `--lines`: Number of lines to display (default: all)

#### Clear DevLog
```bash
python -m dreamos.core.agent_devlog clear AGENT_ID
```
Arguments:
- `AGENT_ID`: The ID of the agent

#### Update DevLog
```bash
python -m dreamos.core.agent_devlog update AGENT_ID "MESSAGE"
```
Arguments:
- `AGENT_ID`: The ID of the agent
- `MESSAGE`: The log message to add

## Examples

### Basic Usage

1. **Check System Status**
```bash
# List all agents
python -m dreamos.core.agent_captain list

# Check specific agent
python -m dreamos.core.agent_captain status Agent-1
```

2. **Send Messages**
```bash
# Send welcome message
python -m dreamos.core.cell_phone_cli --to Agent-1 --welcome

# Send urgent message
python -m dreamos.core.cell_phone_cli --to Agent-1 --message "System alert" --priority 5 --mode URGENT
```

3. **Manage DevLogs**
```bash
# View recent logs
python -m dreamos.core.agent_devlog view Agent-1 --lines 10

# Add log entry
python -m dreamos.core.agent_devlog update Agent-1 "System maintenance completed"
```

### Advanced Usage

1. **Batch Operations**
```bash
# Send messages to multiple agents
for agent in Agent-1 Agent-2 Agent-3; do
    python -m dreamos.core.cell_phone_cli --to $agent --message "System update"
done
```

2. **Status Monitoring**
```bash
# Monitor agent status
while true; do
    python -m dreamos.core.agent_captain status Agent-1
    sleep 60
done
```

3. **Log Analysis**
```bash
# View logs with grep
python -m dreamos.core.agent_devlog view Agent-1 | grep "ERROR"

# Count log entries
python -m dreamos.core.agent_devlog view Agent-1 | wc -l
```

## Error Handling

### Common Errors

1. **Invalid Agent ID**
```bash
Error: Agent not found
```
Solution: Verify agent ID exists

2. **Invalid Priority**
```bash
Error: Priority must be between 0 and 5
```
Solution: Use valid priority value

3. **Invalid Mode**
```bash
Error: Invalid message mode
```
Solution: Use valid mode (NORMAL, URGENT, BROADCAST, SYSTEM)

### Error Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Agent not found |
| 4 | Permission denied |
| 5 | System error |

## Best Practices

### 1. Command Organization
- Use consistent command structure
- Group related commands
- Document command usage

### 2. Error Handling
- Check return codes
- Handle errors gracefully
- Provide helpful messages

### 3. Performance
- Use appropriate options
- Avoid unnecessary commands
- Monitor system load

### 4. Security
- Validate inputs
- Check permissions
- Log security events

## Troubleshooting

### Common Issues

1. **Command Not Found**
- Check Python path
- Verify module installation
- Check virtual environment

2. **Permission Denied**
- Check user permissions
- Verify file access
- Check system settings

3. **Invalid Arguments**
- Check command syntax
- Verify argument values
- Review documentation

### Debugging Tips

1. **Verbose Output**
```bash
# Add --verbose flag
python -m dreamos.core.agent_captain list --verbose
```

2. **Log Files**
```bash
# Check log files
cat /var/log/dreamos/agent_captain.log
```

3. **System Status**
```bash
# Check system status
python -m dreamos.core.agent_captain status
```

## Additional Resources

- [Agent Communication Guide](./agent_communication_guide.md)
- [Agent Development Guide](./agent_development_guide.md)
- [System Architecture Guide](./system_architecture_guide.md) 