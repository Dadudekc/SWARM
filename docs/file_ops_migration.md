# File Operations Migration Guide

## Overview

This document outlines the migration of file operations from the monolithic `serialization.py` to a modular structure. The changes improve maintainability, testability, and code organization while maintaining backward compatibility.

## New Module Structure

```
dreamos/
├── core/
│   ├── io/
│   │   ├── __init__.py
│   │   ├── json_ops.py      # JSON serialization
│   │   ├── yaml_ops.py      # YAML serialization
│   │   └── atomic.py        # Atomic file operations
│   └── utils/
│       ├── __init__.py
│       └── serialization.py  # Legacy compatibility layer
```

## Migration Steps

1. **Update Imports**
   - Replace `from dreamos.core.utils.serialization import *` with specific imports:
   ```python
   from dreamos.core.io.json_ops import load_json, save_json
   from dreamos.core.io.yaml_ops import load_yaml, save_yaml
   from dreamos.core.io.atomic import atomic_write
   ```

2. **Legacy Support**
   - The old `serialization.py` remains as a compatibility layer
   - It re-exports all functions from the new modules
   - No immediate changes required for existing code

3. **New Features**
   - Atomic writes with automatic backup
   - Better error handling and validation
   - Type hints and documentation
   - Improved test coverage

## Breaking Changes

None. The migration is fully backward compatible.

## Testing

Run the test suite to verify compatibility:

```bash
python -m pytest tests/io/
```

## CI Integration

Module size limits are enforced in CI:

```bash
python tools/find_large_modules.py --fail-on-hit
```

## Future Plans

1. **Phase 1 (Complete)**
   - ✅ Split into JSON/YAML/atomic modules
   - ✅ Add type hints and docs
   - ✅ Implement atomic writes

2. **Phase 2 (Planned)**
   - Add schema validation
   - Implement compression support
   - Add async I/O operations

3. **Phase 3 (Planned)**
   - Remove legacy compatibility layer
   - Add streaming support
   - Implement caching layer

## Contributing

When adding new file operations:

1. Place them in the appropriate module
2. Add type hints and docstrings
3. Write unit tests
4. Update this guide

## Support

For questions or issues:
- Open a GitHub issue
- Tag with `file-ops` label
- Reference this guide 