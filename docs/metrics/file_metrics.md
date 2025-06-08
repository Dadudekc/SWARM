# File Operation Metrics

Metrics and logging schema for file operations in Dream.OS.

## Log Events

### File Write

```python
logger.info(
    "file_write",
    extra={
        "path": str,      # File path
        "bytes": int,     # Content size
        "encoding": str,  # File encoding
    }
)
```

### File Write Error

```python
logger.error(
    "file_write_error",
    extra={
        "path": str,    # File path
        "error": str,   # Error message
    }
)
```

### File Read

```python
logger.info(
    "file_read",
    extra={
        "path": str,      # File path
        "bytes": int,     # Content size
        "encoding": str,  # File encoding
    }
)
```

### File Read Error

```python
logger.error(
    "file_read_error",
    extra={
        "path": str,    # File path
        "error": str,   # Error message
    }
)
```

### Directory Operation

```python
logger.info(
    "directory_created",  # or "directory_cleared"
    extra={
        "path": str,    # Directory path
    }
)
```

### Directory Error

```python
logger.error(
    "directory_create_error",  # or "directory_clear_error"
    extra={
        "path": str,    # Directory path
        "error": str,   # Error message
    }
)
```

## Metrics

### Counters

```python
metrics = {
    "file_writes": int,        # Successful writes
    "file_write_errors": int,  # Write failures
    "file_reads": int,         # Successful reads
    "file_read_errors": int,   # Read failures
}
```

### Prometheus Integration

```python
from dreamos.core.metrics import Counter

# File operation counters
file_write_counter = Counter(
    "file_ops_write_total",
    "Total file writes",
    ["path", "operation"]
)

file_read_counter = Counter(
    "file_ops_read_total",
    "Total file reads",
    ["path", "operation"]
)

# Usage
file_write_counter.inc(
    tags={
        "path": "data.txt",
        "operation": "atomic_write"
    }
)
```

## Best Practices

1. **Consistent Fields**: Always include required fields
2. **Error Context**: Include full error details
3. **Path Normalization**: Use absolute paths
4. **Size Tracking**: Log content size for monitoring
5. **Operation Type**: Distinguish between operations

## Example Usage

```python
from dreamos.core.utils.safe_io import atomic_write
from dreamos.core.metrics import Counter

# Initialize counters
write_counter = Counter("file_ops_write_total", ["path", "operation"])

def save_data(path: str, data: str) -> bool:
    """Save data with metrics."""
    try:
        if atomic_write(path, data):
            write_counter.inc(
                tags={
                    "path": path,
                    "operation": "atomic_write"
                }
            )
            return True
        return False
    except Exception as e:
        logger.error(
            "file_write_error",
            extra={
                "path": path,
                "error": str(e)
            }
        )
        return False
``` 