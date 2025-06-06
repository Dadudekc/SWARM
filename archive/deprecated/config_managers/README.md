# Archived Configuration Managers

This directory contains deprecated configuration manager implementations that have been consolidated into the canonical version at `dreamos/core/config/config_manager.py`.

## Archived Files

1. `social_config_manager.py`
   - Original location: `social/utils/config_manager.py`
   - Replaced by: `dreamos/core/config/config_manager.py`
   - Reason: Duplicate functionality, less complete implementation

2. `legacy_social_config.py`
   - Original location: `social/social_config.py`
   - Replaced by: `dreamos/core/config/config_manager.py`
   - Reason: Outdated implementation, functionality merged into core config

3. `social_config_v2.py`
   - Original location: `social/config/social_config.py`
   - Replaced by: `dreamos/core/config/config_manager.py`
   - Reason: Duplicate functionality, less complete implementation

4. `log_config.py`
   - Original location: `social/utils/log_config.py`
   - Replaced by: Logging configuration in `dreamos/core/config/config_manager.py`
   - Reason: Logging config merged into core config manager

## Migration Notes

All configuration management should now use the unified `ConfigManager` class from `dreamos/core/config/config_manager.py`. This implementation provides:

- Unified configuration management
- Bridge-specific configuration
- Enhanced validation
- Better error handling
- Proper file permissions
- Default configuration values

## Usage Example

```python
from dreamos.core.config.config_manager import ConfigManager

# Initialize with default config
config = ConfigManager()

# Get configuration value
log_level = config.get('log_level')

# Set configuration value
config.set('log_level', 'DEBUG')

# Get bridge-specific config
bridge_config = config.get_bridge_config()
```

## Migration Status

- [x] Files archived
- [x] Deprecation warnings added
- [x] Documentation updated
- [x] Imports checked for references

## Next Steps

1. Update any remaining imports to use the canonical version
2. Remove deprecated files once all references are updated
3. Update documentation to reflect the consolidated configuration management 