# File Operations Migration Guide

## Overview

This guide outlines the migration process from scattered file operations to the new centralized `file_ops.py` module. The migration will improve code consistency, error handling, and maintainability.

## Migration Map

### 1. JSON Operations

| Old Pattern | New Pattern | Example |
|------------|-------------|---------|
| `with open(path, 'r') as f: json.load(f)` | `read_json(path, default=None)` | `data = read_json('config.json', {})` |
| `with open(path, 'w') as f: json.dump(data, f)` | `write_json(path, data)` | `write_json('config.json', config)` |

### 2. YAML Operations

| Old Pattern | New Pattern | Example |
|------------|-------------|---------|
| `with open(path, 'r') as f: yaml.safe_load(f)` | `read_yaml(path, default=None)` | `config = read_yaml('config.yaml', {})` |
| `with open(path, 'w') as f: yaml.dump(data, f)` | `write_yaml(path, data)` | `write_yaml('config.yaml', config)` |

### 3. Directory Operations

| Old Pattern | New Pattern | Example |
|------------|-------------|---------|
| `os.makedirs(path, exist_ok=True)` | `ensure_dir(path)` | `ensure_dir('logs')` |
| `shutil.rmtree(path)` | `safe_rmdir(path, recursive=True)` | `safe_rmdir('temp', recursive=True)` |

### 4. File Operations

| Old Pattern | New Pattern | Example |
|------------|-------------|---------|
| `with open(path, mode) as f:` | `with safe_file_handle(path, mode) as f:` | `with safe_file_handle('file.txt', 'r') as f:` |
| Manual file rotation | `rotate_file(path, max_size, max_files)` | `rotate_file('app.log', 10*1024*1024, 5)` |

## Priority Modules for Migration

### High Priority (Core Functionality)

1. `dreamos/core/config.py`
   - Replace YAML loading/saving
   - Update directory creation

2. `dreamos/core/persistent_queue.py`
   - Replace JSON operations
   - Add error handling

3. `dreamos/core/metrics.py`
   - Replace JSON operations
   - Add file rotation

### Medium Priority (Supporting Modules)

1. `dreamos/core/messaging/agent_bus.py`
   - Replace JSON history operations
   - Add error handling

2. `dreamos/core/messaging/captain_phone.py`
   - Replace YAML/JSON operations
   - Update config handling

3. `dreamos/core/autonomy_loop_runner.py`
   - Replace JSON operations
   - Add error handling

### Low Priority (Utility Modules)

1. `dreamos/core/coordinate_utils.py`
   - Replace JSON operations
   - Add error handling

2. `dreamos/core/region_finder.py`
   - Replace JSON operations
   - Add error handling

## Migration Steps

1. **Preparation**
   ```python
   from dreamos.core.utils.file_ops import (
       read_json, write_json,
       read_yaml, write_yaml,
       ensure_dir, safe_rmdir,
       safe_file_handle, rotate_file
   )
   ```

2. **Replace Operations**
   - Replace direct file operations with `file_ops` equivalents
   - Update error handling to use `FileOpsError` hierarchy
   - Add appropriate logging

3. **Testing**
   - Run existing tests
   - Add new tests for error cases
   - Verify cross-platform compatibility

## Example Migration

### Before:
```python
def load_config(config_path):
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {}
```

### After:
```python
def load_config(config_path):
    return read_json(config_path, default={})
```

## Error Handling

The new module provides a consistent error hierarchy:

- `FileOpsError`: Base exception
- `FileOpsPermissionError`: Permission issues
- `FileOpsIOError`: I/O and format issues

Example:
```python
try:
    data = read_json('config.json')
except FileOpsPermissionError:
    logger.error("Permission denied accessing config")
    return {}
except FileOpsIOError:
    logger.error("Error reading config")
    return {}
```

## Testing

1. Run existing tests
2. Add new tests for:
   - Error cases
   - Cross-platform compatibility
   - File rotation
   - Permission handling

## Rollback Plan

1. Keep old implementations in comments
2. Use feature flags if needed
3. Maintain backup of original files

## Timeline

1. **Week 1**: High-priority modules
2. **Week 2**: Medium-priority modules
3. **Week 3**: Low-priority modules and testing

## Support

For questions or issues:
1. Check the module documentation
2. Review test cases
3. Contact the core team 