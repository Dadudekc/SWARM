# Archived Components

This directory contains deprecated components that have been replaced by newer, more feature-complete versions.

## Config Managers

- `config_managers/social_config_manager.py`
  - Original location: `social/utils/config_manager.py`
  - Replaced by: `dreamos/core/config/config_manager.py`
  - Reason: Consolidated into unified config manager with better validation and bridge support

## Message Processors

- `message_processors/legacy_message_processor.py`
  - Original location: `dreamos/core/message_processor.py`
  - Replaced by: `dreamos/core/messaging/message_processor.py`
  - Reason: Newer version has persistent queue, message chunking, retry mechanisms, and better error handling

## DevLog Managers

- `devlog_managers/social_devlog_manager.py`
  - Original location: `social/utils/devlog_manager.py`
  - Replaced by: `dreamos/core/agent_control/devlog_manager.py`
  - Reason: Newer version has Discord integration, task management, real-time updates, and rich formatting

## Usage Notes

1. All archived components have deprecation warnings that point to their replacements
2. Do not use these components in new code
3. If you find code still using these components, update the imports to use the canonical versions
4. These files are kept for reference and to maintain git history

## Config Managers

### Archived Files
- `archive/deprecated/config_managers/legacy_config_manager.py` (from `dreamos/core/shared/config_manager.py`)
- `archive/deprecated/config_managers/social_config.py` (from `social/config/social_config.py`)

### Canonical Version
The canonical configuration manager is now located at:
`social/utils/config_manager.py`

### Migration Notes
- All configuration functionality has been consolidated into `social/utils/config_manager.py`
- The `ConfigManager` class provides all necessary functionality for:
  - Loading and saving configuration
  - Managing config directories
  - Handling default values
  - Validating configuration
- Specialized configs (e.g., social features) should extend the base `ConfigManager`

## Auth Managers

### Archived Files
- `archive/deprecated/auth_managers/legacy_auth_manager.py` (from `src/auth/manager.py`)
- `archive/deprecated/auth_managers/legacy_session.py` (from `src/auth/session.py`)

### Canonical Version
The canonical auth manager is now located at:
`dreamos/core/auth/manager.py`

### Migration Notes
- Authentication functionality has been consolidated into `dreamos/core/auth/`
- The new implementation provides:
  - Unified session management
  - Token handling
  - Retry mechanisms
  - Better error handling

## DevLog Managers

### Archived Files
- `archive/deprecated/devlog_managers/legacy_devlog.py` (from `dreamos/core/devlog.py`)
- `archive/deprecated/devlog_managers/legacy_devlog_manager.py` (from `dreamos/core/agent_control/devlog_manager.py`)

### Canonical Version
The canonical devlog manager is now located at:
`social/utils/devlog_manager.py`

### Migration Notes
- Devlog functionality has been consolidated into `social/utils/devlog_manager.py`
- The new implementation provides:
  - Unified logging interface
  - Better file management
  - Improved metadata handling
  - Support for different formats

## Structure

```
archive/
├── deprecated/
│   ├── config_managers/     # Consolidated into dreamos/core/config/
│   ├── auth_managers/       # Consolidated into dreamos/core/auth/
│   ├── message_processors/  # Consolidated into dreamos/core/messaging/
│   └── devlog_managers/     # Consolidated into dreamos/core/agent_control/
```

## Archived Components

### Config Managers
- Original: `dreamos/core/shared/config_manager.py`
- Original: `social/utils/config_manager.py`
- Canonical: `dreamos/core/config/config_manager.py`

### Auth & Session Managers
- Original: `src/auth/manager.py`
- Original: `src/auth/session.py`
- Canonical: `dreamos/core/auth/manager.py`
- Canonical: `dreamos/core/auth/session.py`

### Message Processors
- Original: `dreamos/core/message_processor.py`
- Canonical: `dreamos/core/messaging/message_processor.py`

### DevLog Managers
- Original: `dreamos/core/devlog.py`
- Original: `social/utils/devlog_manager.py`
- Canonical: `dreamos/core/agent_control/devlog_manager.py`

## Migration Notes

1. All imports should be updated to use the canonical versions
2. Deprecated files include warning messages directing to canonical versions
3. No functionality was removed, only consolidated
4. Test coverage was preserved during migration

## Last Updated
2025-06-05 