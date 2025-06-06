# Archived Code

This directory contains deprecated code that has been superseded by more robust implementations.

## Archived Components

### ResponseLoopDaemon
- **Original Location**: `src/dreamos/core/loop/response_loop_daemon.py`
- **Replaced By**: `dreamos/core/autonomy/bridge_outbox_handler.py`
- **Rationale**: Duplicate functionality with `BridgeOutboxHandler`. The handler provides more robust AST-based code change processing and better integration with the agent loop system.

### ConfigManager
- **Original Locations**:
  - `dreamos/core/config.py`
  - `dreamos/core/shared/config_manager.py`
  - `social/utils/config_manager.py`
- **Canonical Version**: `social/utils/config_manager.py`
- **Rationale**: Multiple implementations with overlapping functionality
- **Migration Notes**:
  - Agent-specific config now handled through configuration sections
  - Test stubs replaced with test-specific configuration
  - All functionality consolidated into single robust implementation

### AuthManager/SessionManager
- **Original Locations**:
  - `src/auth/manager.py` vs. `dreamos/core/auth/manager.py`
  - `src/auth/session.py` vs. `dreamos/core/auth/session.py`
- **Canonical Version**: `dreamos/core/security/auth_manager.py` and `dreamos/core/security/session_manager.py`
- **Rationale**: Duplicate authentication and session management
- **Migration Notes**:
  - Consolidated into unified security namespace
  - Enhanced with proper token management
  - Added role-based access control

### MessageProcessor
- **Original Locations**:
  - `dreamos/core/message_processor.py`
  - `dreamos/core/messaging/message_processor.py`
- **Canonical Version**: `dreamos/core/messaging/message_processor.py`
- **Rationale**: Duplicate message handling logic
- **Migration Notes**:
  - Enhanced with proper validation
  - Added support for different message types
  - Improved error handling

### DevLogManager
- **Original Locations**:
  - `dreamos/core/devlog.py`
  - `social/utils/devlog_manager.py`
  - `dreamos/core/agent_control/devlog_manager.py`
- **Canonical Version**: `dreamos/core/logging/devlog_manager.py`
- **Rationale**: Multiple logging implementations
- **Migration Notes**:
  - Consolidated into unified logging system
  - Added structured logging
  - Improved log rotation

## Migration Status

### Completed
- [x] ConfigManager consolidation
  - Deprecated implementations archived
  - Imports updated to canonical version
  - Documentation updated

### In Progress
- [ ] AuthManager/SessionManager consolidation
- [ ] MessageProcessor consolidation
- [ ] DevLogManager consolidation

### Pending
- [ ] Test file consolidation
- [ ] Utility module consolidation
- [ ] Configuration file consolidation

## Next Steps

1. Complete AuthManager/SessionManager migration
2. Consolidate MessageProcessor implementations
3. Merge DevLogManager variants
4. Clean up test files
5. Consolidate utility modules
6. Unify configuration files

## Usage Instructions

For each component, refer to its specific README in the corresponding archive directory for detailed migration instructions and usage examples.

## Migration Notes

### ResponseLoopDaemon → BridgeOutboxHandler
- Use `BridgeOutboxHandler` for all agent response processing
- The handler provides:
  - AST-based code change processing
  - Automatic test validation
  - Git commit integration
  - Better error handling and retries
  - Integration with the agent loop system

## Usage

To process agent responses, use the `BridgeOutboxHandler`:

```python
from dreamos.core.autonomy.bridge_outbox_handler import BridgeOutboxHandler

handler = BridgeOutboxHandler()
await handler.start()  # Start processing responses
```

The handler will:
1. Watch for new agent responses
2. Parse and validate code changes
3. Apply changes using AST
4. Run tests
5. Commit successful changes

## Next Steps

1. Create migration scripts for each duplicated component
2. Update imports across the codebase
3. Add deprecation warnings to old implementations
4. Gradually migrate to consolidated components
5. Remove deprecated code after migration period

## Migration Progress

### ConfigManager Migration
1. ✅ Added deprecation warnings to:
   - `dreamos/core/config.py`
   - `dreamos/core/shared/config_manager.py`
2. ✅ Updated `dreamos/core/shared/__init__.py` to use canonical implementation
3. ✅ Verified no direct imports of deprecated modules
4. ✅ Archived deprecated implementations to `archive/deprecated/config_managers/`
5. ✅ Added detailed documentation in archive

### Auth & Session Manager Migration
1. ✅ Archived all implementations to `archive/deprecated/auth_managers/`:
   - `legacy_auth_manager.py`
   - `core_auth_manager.py`
   - `legacy_session_manager.py`
   - `core_session_manager.py`
2. ✅ Added detailed documentation in archive
3. ⏳ Ready for new security namespace implementation

### Next Component to Migrate
- MessageProcessor
- DevLogManager 