# Dream.OS Logging System

## Overview

The Dream.OS logging system provides comprehensive logging capabilities across all components, from Discord commands to GUI monitoring. It enables real-time monitoring, debugging, and analysis of system operations.

## Quick Start

```python
from social.utils.log_manager import LogManager
from social.utils.log_config import LogConfig

# Initialize with default config
log = LogManager("agent1").get_logger()
log.info("System initialized")

# Or with custom config
config = LogConfig(
    log_dir="logs/custom",
    batch_size=10,
    batch_timeout=0.5
)
log = LogManager("agent1", config=config).get_logger()
log.info("Custom logging initialized")
```

## Viewing Logs

### Discord Commands
```bash
# View logs for a specific agent
!logs agent1 error

# View all logs with warning level
!logs all warning

# View recent logs with limit
!logs agent1 info 20

# Get log summary
!logsummary agent1
```

### GUI Dashboard
1. Launch the dashboard:
```bash
python -m gui
```

2. Use the LogMonitor tab to:
   - Filter logs by platform/level
   - View detailed log information
   - Clear logs
   - Auto-refresh

### Command Line
```bash
# Analyze logs for an agent
python scripts/analyze_logs.py --agent agent1 --level error --summary

# Export as markdown
python scripts/analyze_logs.py --agent agent1 --summary --export md

# Export as JSON
python scripts/analyze_logs.py --agent agent1 --summary --export json
```

## Failure Recovery

### Common Issues

1. **Log File Not Found**
   - Check `logs/agent_loop_error.log`
   - Verify agent ID is correct
   - Ensure log directory exists

2. **Log Rotation Issues**
   - Clear old logs: `python scripts/analyze_logs.py --agent agent1 --clear`
   - Rotate logs: `python scripts/analyze_logs.py --agent agent1 --rotate`

3. **System Validation**
   - Run test suite: `python -m pytest tests/core/test_log_manager.py`
   - Check log permissions
   - Verify disk space

### Recovery Steps

1. **Immediate Actions**
   ```bash
   # Check error logs
   !logs agent1 error
   
   # Validate system
   python -m pytest tests/core/test_log_manager.py
   
   # Clear and rotate if needed
   python scripts/analyze_logs.py --agent agent1 --clear --rotate
   ```

2. **System Check**
   - Verify log directory permissions
   - Check disk space
   - Validate log file integrity

3. **Revalidation**
   - Run test suite
   - Check log rotation
   - Verify log writing

## Components

### 1. Discord Commander

```bash
# View logs for a specific agent
!logs agent1 error

# View all logs with warning level
!logs all warning

# View recent logs with limit
!logs agent1 info 20
```

### 2. Devlog System

The devlog system bridges execution logs with storytelling, writing key events to `devlog.md`:

```python
# Log an event
log_manager.log_event(agent_id, "task_completed", {
    "task_id": "task_123",
    "duration": "5m",
    "status": "success"
})
```

### 3. Social Memory

Logs feed into the `memory_update` structure for real-time state reflection:

```python
memory_update["last_action"] = {
    "action": "post",
    "success": True,
    "timestamp": "2024-03-19T12:00:00Z"
}
```

### 4. GUI Dashboard

The LogMonitor component provides:
- Real-time log tailing
- Log level filtering
- Platform/agent selection
- Detail pane
- Auto-refresh

## Usage

### Discord Commands

```bash
# View logs
!logs <agent_id> <level> [limit]

# Examples
!logs agent1 error
!logs all warning 50
!logs social info
```

### GUI Dashboard

1. Launch the dashboard:
```bash
python -m gui
```

2. Use the LogMonitor tab to:
   - Filter logs by platform/level
   - View detailed log information
   - Clear logs
   - Auto-refresh

### Programmatic Usage

```python
from social.utils.log_manager import LogManager
from social.utils.log_config import LogConfig

# Initialize LogManager
log_config = LogConfig(
    log_dir="logs/custom",
    batch_size=10,
    batch_timeout=0.5,
    max_retries=2,
    retry_delay=0.1
)
log_manager = LogManager(config=log_config)

# Log events
log_manager.info(
    platform="custom",
    status="event",
    message="Custom event message",
    metadata={"key": "value"}
)

# Read logs
logs = log_manager.read_logs(
    platform="custom",
    level="INFO",
    limit=100
)
```

## Configuration

### Log Levels

- DEBUG: Detailed debugging information
- INFO: General operational information
- WARNING: Warning messages
- ERROR: Error messages

### Platforms

- agent_loop: Agent execution logs
- social: Social media operations
- devlog: Development logs
- discord: Discord bot operations
- gui: GUI dashboard operations

## Future Enhancements

1. Task Integration
   - Add task ID tracking
   - Cross-reference agent logs with active tasks

2. Export Capabilities
   - Download .log files
   - Export filtered views as .md or .json

3. Smart Summarization
   - Auto-summarize recent logs
   - Generate health reports
   - Track error frequencies

## Contributing

1. Follow the logging standards
2. Add appropriate metadata
3. Use correct log levels
4. Include error details when relevant

## Support

For issues or questions, please:
1. Check the documentation
2. Review existing logs
3. Open an issue with relevant details 