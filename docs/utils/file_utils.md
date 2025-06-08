# File Utilities

Core file operation utilities for Dream.OS.

## Atomic File Operations

The `safe_io` module provides atomic file operations to ensure data integrity:

```python
from dreamos.core.utils.safe_io import atomic_write, safe_read

# Atomic write with encoding
atomic_write("data.txt", "content", encoding="utf-8")

# Safe read with default
content = safe_read("data.txt", default="")
```

### Features

- **Atomic Writes**: Uses temporary files and atomic rename for safe writes
- **Encoding Support**: UTF-8 by default, configurable per operation
- **Error Handling**: Graceful failure with cleanup
- **Metrics**: Operation counts and error tracking

## Directory Operations

The `file_ops` module provides safe directory operations with concurrency protection:

```python
from dreamos.core.utils.file_ops import safe_mkdir, ensure_dir

# Create directory with lock
safe_mkdir("data/dir")

# Ensure directory exists
ensure_dir("data/dir")
```

### Features

- **Concurrency Safety**: Uses `InterProcessLock` for thread/process safety
- **Error Handling**: Specific exceptions for common errors
- **Atomic Operations**: Safe directory creation and cleanup

## Logging and Metrics

File operations emit structured logs and metrics:

```python
# Log example
logger.info(
    "file_write",
    extra={
        "path": "data.txt",
        "bytes": 1024,
        "encoding": "utf-8"
    }
)

# Metrics
metrics["file_writes"] += 1
```

### Log Fields

- `path`: File path
- `bytes`: Content size
- `encoding`: File encoding
- `error`: Error message (if any)

### Metrics

- `file_writes`: Total successful writes
- `file_write_errors`: Write failures
- `file_reads`: Total successful reads
- `file_read_errors`: Read failures

## Best Practices

1. **Always use atomic writes** for data files
2. **Handle encoding explicitly** for text files
3. **Use safe_mkdir** for directory creation
4. **Check return values** for operation success
5. **Monitor metrics** for operation health

## Examples

### Safe File Write

```python
from dreamos.core.utils.safe_io import atomic_write

def save_data(path: str, data: str) -> bool:
    """Save data to file safely."""
    return atomic_write(
        path,
        data,
        encoding="utf-8"
    )
```

### Safe Directory Creation

```python
from dreamos.core.utils.file_ops import safe_mkdir

def setup_data_dir(path: str) -> None:
    """Create data directory safely."""
    safe_mkdir(path)
```

### File Roundtrip

```python
from dreamos.core.utils.safe_io import atomic_write, safe_read

def update_file(path: str, content: str) -> bool:
    """Update file with backup."""
    # Read existing
    old = safe_read(path, default="")
    
    # Write new
    if atomic_write(path, content):
        return True
        
    # Restore on failure
    atomic_write(path, old)
    return False
``` 