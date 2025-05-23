# Agent DevLog Guide

## Overview
The DevLog system allows agents to maintain a development log of their activities and automatically notify the team via Discord. This guide explains how to use the DevLog system effectively.

## Basic Usage

### 1. Initializing the Logger
```python
from dreamos.core.agent_logger import AgentLogger

# Initialize logger with your agent ID
logger = AgentLogger("Agent-2")  # Replace with your agent ID
```

### 2. Making Log Entries
```python
# Basic log entry
logger.log("Starting new task")

# Log with category
logger.log("Task completed successfully", category="SUCCESS")

# Log with metadata
logger.log(
    "Processing data batch",
    category="PROCESS",
    metadata={
        "batch_size": 1000,
        "processing_time": "2.5s",
        "status": "completed"
    }
)
```

## Log Categories

Use these standard categories for consistent logging:

- `INIT`: Initialization and startup events
- `INFO`: General information and updates
- `TASK`: Task-related events
- `PROCESS`: Processing and computation events
- `SUCCESS`: Successful operations
- `WARNING`: Potential issues or concerns
- `ERROR`: Error conditions
- `DEBUG`: Debugging information
- `SYSTEM`: System-level events
- `COLLAB`: Inter-agent collaboration events

## Best Practices

### 1. Message Format
- Be clear and concise
- Include relevant context
- Use proper punctuation
- Start with a verb when describing actions

Examples:
```python
# Good
logger.log("Completed data analysis for batch #123", category="SUCCESS")
logger.log("Detected potential optimization in task queue", category="WARNING")

# Avoid
logger.log("done", category="SUCCESS")  # Too vague
logger.log("error happened", category="ERROR")  # Not descriptive enough
```

### 2. Metadata Usage
Include relevant metadata to provide additional context:

```python
# Task completion
logger.log(
    "Completed task processing",
    category="SUCCESS",
    metadata={
        "task_id": "TASK-123",
        "duration": "1.5s",
        "resources_used": {
            "cpu": "45%",
            "memory": "128MB"
        }
    }
)

# Error reporting
logger.log(
    "Failed to process data batch",
    category="ERROR",
    metadata={
        "error_code": "E-1001",
        "batch_id": "BATCH-456",
        "retry_count": 3,
        "error_details": "Connection timeout"
    }
)
```

### 3. Regular Updates
- Log significant state changes
- Report task progress
- Document important decisions
- Record collaboration events

## Common Use Cases

### 1. Task Processing
```python
# Start of task
logger.log(
    "Starting new task",
    category="TASK",
    metadata={"task_id": "TASK-789", "priority": "high"}
)

# Task progress
logger.log(
    "Task progress update",
    category="INFO",
    metadata={
        "task_id": "TASK-789",
        "progress": "75%",
        "estimated_completion": "2 minutes"
    }
)

# Task completion
logger.log(
    "Task completed successfully",
    category="SUCCESS",
    metadata={
        "task_id": "TASK-789",
        "duration": "5.2s",
        "results": {"processed_items": 1000}
    }
)
```

### 2. System Events
```python
# System startup
logger.log(
    "System initialization complete",
    category="INIT",
    metadata={
        "version": "1.0.0",
        "components": ["core", "memory", "processor"],
        "startup_time": "1.2s"
    }
)

# Resource monitoring
logger.log(
    "Resource usage alert",
    category="WARNING",
    metadata={
        "resource": "memory",
        "usage": "85%",
        "threshold": "80%",
        "action_taken": "initiated_cleanup"
    }
)
```

### 3. Collaboration
```python
# Inter-agent communication
logger.log(
    "Received collaboration request",
    category="COLLAB",
    metadata={
        "from_agent": "Agent-1",
        "request_type": "data_processing",
        "priority": "medium"
    }
)

# Collaboration completion
logger.log(
    "Completed collaborative task",
    category="COLLAB",
    metadata={
        "with_agent": "Agent-1",
        "task_type": "data_processing",
        "results": {"processed_items": 500}
    }
)
```

## Error Handling

### 1. Logging Errors
```python
try:
    # Your code here
    result = process_data()
except Exception as e:
    logger.log(
        f"Error processing data: {str(e)}",
        category="ERROR",
        metadata={
            "error_type": type(e).__name__,
            "stack_trace": traceback.format_exc(),
            "context": {
                "data_id": "DATA-123",
                "processing_stage": "validation"
            }
        }
    )
```

### 2. Recovery Actions
```python
# Log recovery attempt
logger.log(
    "Initiating recovery procedure",
    category="SYSTEM",
    metadata={
        "error_id": "E-1001",
        "recovery_type": "automatic",
        "attempt": 1
    }
)

# Log recovery result
logger.log(
    "Recovery completed successfully",
    category="SUCCESS",
    metadata={
        "error_id": "E-1001",
        "recovery_type": "automatic",
        "duration": "1.5s"
    }
)
```

## Viewing and Managing Logs

### 1. Reading Logs
```python
# Get entire log
log_content = logger.get_log()

# Process log content
if log_content:
    # Parse and analyze log entries
    pass
```

### 2. Clearing Logs
```python
# Clear log with backup
success = logger.clear_log()
if success:
    print("Log cleared successfully")
else:
    print("Failed to clear log")
```

## Discord Integration

The DevLog system automatically sends updates to the configured Discord channel. Your log entries will appear as formatted embeds with:
- Title showing your agent ID
- Log message
- Category
- Metadata (if provided)
- Timestamp

## Troubleshooting

### Common Issues

1. **Log Not Appearing in Discord**
   - Check if the Discord channel is properly configured
   - Verify the message format is correct
   - Ensure the agent has proper permissions

2. **Metadata Not Showing**
   - Verify the metadata is a valid dictionary
   - Check for any non-serializable objects
   - Ensure the metadata size is reasonable

3. **Log File Issues**
   - Check file permissions
   - Verify the log directory exists
   - Ensure sufficient disk space

## Support

If you encounter any issues with the DevLog system:
1. Check the error logs
2. Review the Discord channel for any error messages
3. Contact the system administrator

Remember: Good logging practices help the entire team understand your agent's activities and troubleshoot issues more effectively. 