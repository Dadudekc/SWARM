# Bridge Architecture Reorganization

## 1. Directory Structure

```
dreamos/
├── core/
│   └── bridge/                    # All bridge-related code
│       ├── __init__.py
│       ├── base/                  # Base classes and interfaces
│       │   ├── __init__.py
│       │   ├── bridge.py         # Base bridge interface
│       │   ├── handler.py        # Base handler interface
│       │   └── processor.py      # Base processor interface
│       ├── chatgpt/              # ChatGPT integration
│       │   ├── __init__.py
│       │   ├── bridge.py         # ChatGPT bridge implementation
│       │   ├── prompt.py         # Prompt management
│       │   └── templates/        # Jinja2 templates
│       ├── handlers/             # Bridge handlers
│       │   ├── __init__.py
│       │   ├── outbox.py         # Outbox handler
│       │   └── inbox.py          # Inbox handler
│       ├── processors/           # Response processors
│       │   ├── __init__.py
│       │   ├── base.py          # Base processor
│       │   ├── core.py          # Core processor
│       │   └── bridge.py        # Bridge processor
│       └── monitoring/           # Monitoring and metrics
│           ├── __init__.py
│           ├── metrics.py        # Metrics collection
│           └── health.py         # Health monitoring
└── bridge/                       # Bridge CLI and utilities
    ├── __init__.py
    ├── cli.py                    # Command-line interface
    └── utils.py                  # Utility functions
```

## 2. Component Consolidation

### 2.1 Bridge Implementation
- Consolidate all `ChatGPTBridge` implementations into `core/bridge/chatgpt/bridge.py`
- Single source of truth for bridge functionality
- Clear interface through base classes

### 2.2 Response Loop
- Single `ResponseLoop` implementation in `core/bridge/base/loop.py`
- Configurable through processor and handler injection
- No duplicate implementations

### 2.3 Handlers
- Unified `BridgeHandler` in `core/bridge/handlers/base.py`
- Specialized handlers inherit from base
- Clear separation of concerns

### 2.4 Processors
- Single processor hierarchy in `core/bridge/processors/`
- Factory pattern for creating processors
- No duplicate implementations

## 3. Migration Plan

1. **Phase 1: Base Structure**
   - Create new directory structure
   - Move base classes and interfaces
   - Update imports

2. **Phase 2: Component Migration**
   - Migrate ChatGPT bridge
   - Migrate response loop
   - Migrate handlers
   - Migrate processors

3. **Phase 3: Cleanup**
   - Remove duplicate implementations
   - Update documentation
   - Add tests

4. **Phase 4: Validation**
   - Verify all functionality
   - Performance testing
   - Security review

## 4. Benefits

1. **Reduced Duplication**
   - Single implementation of each component
   - Clear inheritance hierarchy
   - Shared utilities

2. **Better Organization**
   - Logical component grouping
   - Clear dependencies
   - Easy to find code

3. **Improved Maintainability**
   - Centralized changes
   - Consistent patterns
   - Better testing

4. **Enhanced Extensibility**
   - Clear extension points
   - Plugin architecture
   - Version control

## 5. Implementation Notes

1. **Backward Compatibility**
   - Maintain existing interfaces
   - Gradual migration
   - Deprecation warnings

2. **Testing Strategy**
   - Unit tests for each component
   - Integration tests for flows
   - Performance benchmarks

3. **Documentation**
   - API documentation
   - Architecture diagrams
   - Migration guides

4. **Monitoring**
   - Health checks
   - Metrics collection
   - Error tracking 