# Dream.OS Codebase Reorganization Plan

## Phase 1: Preparation

### 1.1 Create New Directory Structure
```bash
# Create new directory structure
mkdir -p dreamos/core/{agent,automation,bridge,messaging,monitoring,utils}
mkdir -p dreamos/config/{agent,bridge,system}
mkdir -p dreamos/tests/{unit,integration,e2e}
```

### 1.2 Update Configuration
- Move configuration files to appropriate directories
- Update configuration paths in code
- Create configuration validation

## Phase 2: Core Component Migration

### 2.1 Agent System
- Move agent control files to `core/agent/control/`
- Move lifecycle management to `core/agent/lifecycle/`
- Move state management to `core/agent/state/`

### 2.2 Automation System
- Move browser automation to `core/automation/browser/`
- Move chat automation to `core/automation/chat/`
- Move UI automation to `core/automation/ui/`

### 2.3 Bridge System
- Move ChatGPT integration to `core/bridge/chatgpt/`
- Move Cursor integration to `core/bridge/cursor/`
- Move bridge handlers to `core/bridge/handlers/`

### 2.4 Messaging System
- Move message queues to `core/messaging/queue/`
- Move message handlers to `core/messaging/handlers/`
- Move message processors to `core/messaging/processors/`

### 2.5 Monitoring System
- Move health checks to `core/monitoring/health/`
- Move metrics to `core/monitoring/metrics/`
- Move logging to `core/monitoring/logging/`

## Phase 3: Configuration Migration

### 3.1 Agent Configuration
- Move agent configs to `config/agent/`
- Update agent config references
- Validate agent configs

### 3.2 Bridge Configuration
- Move bridge configs to `config/bridge/`
- Update bridge config references
- Validate bridge configs

### 3.3 System Configuration
- Move system configs to `config/system/`
- Update system config references
- Validate system configs

## Phase 4: Documentation Migration

### 4.1 Architecture Documentation
- Move architecture docs to `docs/architecture/`
- Update documentation references
- Validate documentation links

### 4.2 API Documentation
- Move API docs to `docs/api/`
- Update API documentation
- Validate API examples

### 4.3 User Guides
- Move user guides to `docs/guides/`
- Update guide references
- Validate guide content

## Phase 5: Testing Migration

### 5.1 Unit Tests
- Move unit tests to `tests/unit/`
- Update test imports
- Run test suite

### 5.2 Integration Tests
- Move integration tests to `tests/integration/`
- Update test imports
- Run test suite

### 5.3 End-to-End Tests
- Move E2E tests to `tests/e2e/`
- Update test imports
- Run test suite

## Phase 6: Cleanup and Validation

### 6.1 Code Cleanup
- Remove deprecated files
- Update import statements
- Fix broken references

### 6.2 Validation
- Run full test suite
- Validate configurations
- Check documentation

### 6.3 Final Steps
- Update README files
- Create migration guide
- Document changes

## Migration Steps

1. **Preparation**
   ```bash
   # Create backup
   tar -czf dreamos_backup.tar.gz dreamos/
   
   # Create new structure
   mkdir -p dreamos/core/{agent,automation,bridge,messaging,monitoring,utils}
   mkdir -p dreamos/config/{agent,bridge,system}
   mkdir -p dreamos/tests/{unit,integration,e2e}
   ```

2. **Component Migration**
   ```bash
   # Move agent components
   mv dreamos/core/agent_control/* dreamos/core/agent/control/
   mv dreamos/core/autonomy/* dreamos/core/agent/lifecycle/
   mv dreamos/core/agent_state.py dreamos/core/agent/state/
   
   # Move automation components
   mv dreamos/core/automation/browser_control.py dreamos/core/automation/browser/
   mv dreamos/core/automation/chat_* dreamos/core/automation/chat/
   mv dreamos/core/ui/* dreamos/core/automation/ui/
   
   # Move bridge components
   mv dreamos/core/bridge/chatgpt/* dreamos/core/bridge/chatgpt/
   mv dreamos/core/bridge/cursor/* dreamos/core/bridge/cursor/
   mv dreamos/core/bridge/handlers/* dreamos/core/bridge/handlers/
   ```

3. **Configuration Migration**
   ```bash
   # Move configurations
   mv config/agent_* config/agent/
   mv config/bridge_* config/bridge/
   mv config/system_* config/system/
   ```

4. **Documentation Migration**
   ```bash
   # Move documentation
   mv docs/architecture/* docs/architecture/
   mv docs/api/* docs/api/
   mv docs/guides/* docs/guides/
   ```

5. **Testing Migration**
   ```bash
   # Move tests
   mv tests/unit/* tests/unit/
   mv tests/integration/* tests/integration/
   mv tests/e2e/* tests/e2e/
   ```

## Validation Checklist

- [ ] All components moved to new locations
- [ ] Import statements updated
- [ ] Configuration paths updated
- [ ] Documentation links fixed
- [ ] Tests passing
- [ ] No broken references
- [ ] README files updated
- [ ] Migration guide created
- [ ] Changes documented 