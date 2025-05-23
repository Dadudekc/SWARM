# Agent Tasks Guide

## Overview
This guide explains how to handle tasks in the Dream.OS agent network, including task reception, processing, and reporting.

## Task Types

### 1. Standard Tasks
```python
# Receive standard task
task = {
    "type": "STANDARD",
    "id": "TASK-123",
    "description": "Process data batch",
    "priority": "normal",
    "deadline": "2024-03-20T12:00:00"
}
```

### 2. Collaborative Tasks
```python
# Receive collaborative task
task = {
    "type": "COLLAB",
    "id": "TASK-124",
    "description": "Joint data analysis",
    "collaborators": ["Agent-1", "Agent-3"],
    "priority": "high"
}
```

### 3. System Tasks
```python
# Receive system task
task = {
    "type": "SYSTEM",
    "id": "TASK-125",
    "description": "System maintenance",
    "priority": "critical",
    "requires_approval": true
}
```

## Task Processing

### 1. Task Reception
```python
# Log task receipt
logger.log(
    "Received new task",
    category="TASK",
    metadata={
        "task_id": task["id"],
        "type": task["type"],
        "priority": task["priority"]
    }
)
```

### 2. Task Validation
```python
# Validate task
def validate_task(task):
    required_fields = ["id", "type", "description", "priority"]
    return all(field in task for field in required_fields)

# Log validation result
if validate_task(task):
    logger.log(
        "Task validated successfully",
        category="TASK",
        metadata={"task_id": task["id"]}
    )
else:
    logger.log(
        "Task validation failed",
        category="ERROR",
        metadata={"task_id": task["id"]}
    )
```

### 3. Task Execution
```python
# Execute task
async def execute_task(task):
    try:
        # Log start
        logger.log(
            "Starting task execution",
            category="TASK",
            metadata={"task_id": task["id"]}
        )
        
        # Process task
        result = await process_task(task)
        
        # Log completion
        logger.log(
            "Task completed successfully",
            category="SUCCESS",
            metadata={
                "task_id": task["id"],
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        logger.log(
            f"Task execution failed: {str(e)}",
            category="ERROR",
            metadata={
                "task_id": task["id"],
                "error": str(e)
            }
        )
        raise
```

## Task Management

### 1. Task Queue
```python
# Add to queue
task_queue.append(task)
logger.log(
    "Task added to queue",
    category="TASK",
    metadata={
        "task_id": task["id"],
        "queue_position": len(task_queue)
    }
)
```

### 2. Priority Handling
```python
# Sort by priority
priority_order = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3
}

task_queue.sort(key=lambda x: priority_order[x["priority"]])
```

### 3. Deadline Management
```python
# Check deadlines
def check_deadlines():
    current_time = datetime.now()
    for task in task_queue:
        if task["deadline"] < current_time:
            logger.log(
                "Task deadline passed",
                category="WARNING",
                metadata={
                    "task_id": task["id"],
                    "deadline": task["deadline"]
                }
            )
```

## Task Reporting

### 1. Progress Updates
```python
# Send progress update
def update_progress(task_id, progress):
    logger.log(
        "Task progress update",
        category="INFO",
        metadata={
            "task_id": task_id,
            "progress": f"{progress}%",
            "timestamp": datetime.now().isoformat()
        }
    )
```

### 2. Completion Report
```python
# Generate completion report
def generate_report(task):
    return {
        "task_id": task["id"],
        "completion_time": datetime.now().isoformat(),
        "status": "completed",
        "results": task.get("results", {}),
        "metrics": {
            "duration": task.get("duration"),
            "resources_used": task.get("resources")
        }
    }
```

### 3. Error Reporting
```python
# Report error
def report_error(task, error):
    logger.log(
        f"Task error: {str(error)}",
        category="ERROR",
        metadata={
            "task_id": task["id"],
            "error_type": type(error).__name__,
            "error_details": str(error),
            "stack_trace": traceback.format_exc()
        }
    )
```

## Best Practices

### 1. Task Organization
- Maintain clear task queues
- Prioritize effectively
- Track dependencies
- Monitor deadlines

### 2. Resource Management
- Monitor resource usage
- Handle concurrent tasks
- Implement timeouts
- Clean up resources

### 3. Error Handling
- Implement retry logic
- Log all errors
- Report critical issues
- Maintain task state

## Troubleshooting

### Common Issues

1. **Task Not Starting**
   - Check task validation
   - Verify resource availability
   - Review task queue
   - Check system status

2. **Task Stuck**
   - Monitor progress
   - Check for deadlocks
   - Review resource usage
   - Verify dependencies

3. **Task Failure**
   - Check error logs
   - Review task parameters
   - Verify system state
   - Check resource limits

## Support

If you encounter task-related issues:
1. Check the task logs
2. Review the devlog
3. Contact the system administrator

Remember: Proper task management is crucial for system efficiency. Always maintain clear records and report issues promptly. 