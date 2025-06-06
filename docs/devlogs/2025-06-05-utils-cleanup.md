# Utils Directory Cleanup Plan

## Current State

### Core Utils (`dreamos/core/utils/`)
- `file_utils.py`: Comprehensive file operations
- `retry_utils.py`: Retry logic for operations
- `coordinate_utils.py`: Coordinate system utilities

### Social Utils (`social/utils/`)
- Multiple logging-related files
- Configuration management
- Media validation
- Rate limiting
- Social platform utilities

## Cleanup Actions

### 1. File Operations Consolidation
- [ ] Move `json_settings.py` functionality into `file_utils.py`
- [ ] Enhance JSON/YAML handling in `file_utils.py`
- [ ] Add type hints and documentation
- [ ] Add unit tests
- [ ] Archive `json_settings.py`

### 2. Logging System Consolidation
- [ ] Create new structure under `dreamos/core/logging/`:
  ```
  logging/
  ├── __init__.py
  ├── config.py        # Logging configuration
  ├── manager.py       # Main logging manager
  ├── handlers/        # Log handlers
  │   ├── __init__.py
  │   ├── file.py     # File handler
  │   ├── discord.py  # Discord handler
  │   └── metrics.py  # Metrics handler
  ├── formatters/      # Log formatters
  │   ├── __init__.py
  │   └── json.py     # JSON formatter
  └── utils/          # Logging utilities
      ├── __init__.py
      ├── rotation.py # Log rotation
      └── batching.py # Log batching
  ```
- [ ] Migrate functionality from social utils
- [ ] Add comprehensive tests
- [ ] Archive old logging files

### 3. Configuration Management
- [ ] Move useful features from `json_settings.py` to `config_manager.py`
- [ ] Add support for nested configuration
- [ ] Add validation and schema support
- [ ] Add migration utilities
- [ ] Archive old config files

### 4. Media & Social Utilities
- [ ] Move `media_validator.py` to `dreamos/core/media/`
- [ ] Move `rate_limiter.py` to `dreamos/core/rate_limiting/`
- [ ] Move `social_common.py` to `dreamos/core/social/`
- [ ] Add tests for each module
- [ ] Archive old files

## Migration Steps

1. **Phase 1: Preparation**
   - Create new directory structure
   - Set up test infrastructure
   - Create migration utilities

2. **Phase 2: Core Migration**
   - Move and enhance file operations
   - Consolidate logging system
   - Update configuration management

3. **Phase 3: Social Migration**
   - Move media validation
   - Move rate limiting
   - Move social utilities

4. **Phase 4: Cleanup**
   - Archive deprecated files
   - Update imports
   - Verify tests
   - Update documentation

## Success Criteria
- All functionality preserved
- Tests passing
- No duplicate code
- Clear documentation
- Easy migration path

## Timeline
- Phase 1: 1 day
- Phase 2: 2 days
- Phase 3: 1 day
- Phase 4: 1 day

Total: 5 days

---

*Logged by: Agent-1*
*Date: 2025-06-05*
*Type: Infrastructure* 