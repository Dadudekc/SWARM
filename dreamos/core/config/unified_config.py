"""Unified configuration system for Dream.OS."""

from __future__ import annotations

import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, TypeVar, Generic, Union, Type
from dataclasses import dataclass, field

from ..utils.metrics import metrics, logger, log_operation
from ..utils.exceptions import handle_error
from ..utils.file_ops import FileManager, read_json, write_json, read_text, write_text

T = TypeVar('T')

# Metrics
config_metrics = {
    'load': metrics.counter(
        'config_load_total',
        'Total configuration loads',
        ['name', 'format']
    ),
    'save': metrics.counter(
        'config_save_total',
        'Total configuration saves',
        ['name', 'format']
    ),
    'error': metrics.counter(
        'config_error_total',
        'Total configuration errors',
        ['name', 'operation', 'error_type']
    ),
    'duration': metrics.histogram(
        'config_duration_seconds',
        'Configuration operation duration',
        ['operation']
    )
}

@dataclass
class ConfigValue(Generic[T]):
    """A configuration value with metadata."""
    value: T
    description: str
    default: T
    last_modified: datetime = field(default_factory=datetime.now)
    validation_rules: Optional[Dict[str, Any]] = None

class ConfigSection:
    """A section of configuration values."""
    
    def __init__(self, name: str):
        """Initialize a configuration section.
        
        Args:
            name: Name of the section
        """
        self.name = name
        self._values: Dict[str, ConfigValue] = {}
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        if key in self._values:
            return self._values[key].value
        return default
        
    def set(self, key: str, value: Any, description: str = "", validation_rules: Optional[Dict[str, Any]] = None) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            description: Description of the value
            validation_rules: Optional validation rules
        """
        if key in self._values:
            self._values[key].value = value
            self._values[key].last_modified = datetime.now()
        else:
            self._values[key] = ConfigValue(
                value=value,
                description=description,
                default=value,
                validation_rules=validation_rules
            )
            
    def validate(self) -> bool:
        """Validate all configuration values.
        
        Returns:
            True if all values are valid
        """
        for key, config_value in self._values.items():
            if config_value.validation_rules:
                if not self._validate_value(key, config_value):
                    return False
        return True
        
    def _validate_value(self, key: str, config_value: ConfigValue) -> bool:
        """Validate a configuration value.
        
        Args:
            key: Configuration key
            config_value: Configuration value to validate
            
        Returns:
            True if value is valid
        """
        try:
            rules = config_value.validation_rules
            if not rules:
                return True
                
            value = config_value.value
            
            # Type validation
            if 'type' in rules:
                if not isinstance(value, rules['type']):
                    logger.error(f"Invalid type for {key}: expected {rules['type']}, got {type(value)}")
                    return False
                    
            # Range validation
            if 'min' in rules and value < rules['min']:
                logger.error(f"Value too small for {key}: {value} < {rules['min']}")
                return False
            if 'max' in rules and value > rules['max']:
                logger.error(f"Value too large for {key}: {value} > {rules['max']}")
                return False
                
            # Enum validation
            if 'enum' in rules and value not in rules['enum']:
                logger.error(f"Invalid value for {key}: {value} not in {rules['enum']}")
                return False
                
            return True
            
        except Exception as e:
            error = handle_error(e, {
                "key": key,
                "operation": "validate_value"
            })
            logger.error(f"Error validating {key}: {str(error)}")
            config_metrics['error'].labels(
                name=self.name,
                operation="validate",
                error_type=error.__class__.__name__
            ).inc()
            return False

class UnifiedConfigManager:
    """Unified configuration manager for Dream.OS."""
    
    def __init__(
        self,
        config_dir: Union[str, Path],
        default_format: str = "yaml"
    ):
        """Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
            default_format: Default file format ("yaml" or "json")
        """
        self.config_dir = Path(config_dir)
        self.default_format = default_format
        self._sections: Dict[str, ConfigSection] = {}
        self._file_manager = FileManager[Dict[str, Any]](self.config_dir / "config.json")
        
    def get_section(self, name: str) -> ConfigSection:
        """Get or create a configuration section.
        
        Args:
            name: Name of the section
            
        Returns:
            Configuration section
        """
        if name not in self._sections:
            self._sections[name] = ConfigSection(name)
        return self._sections[name]
        
    @log_operation('config_load', metrics=config_metrics['load'], duration=config_metrics['duration'])
    def load_config(self, name: str, format: Optional[str] = None) -> bool:
        """Load a configuration file.
        
        Args:
            name: Name of the configuration file (without extension)
            format: Optional file format override
            
        Returns:
            True if configuration loaded successfully
        """
        try:
            format = format or self.default_format
            path = self.config_dir / f"{name}.{format}"
            
            if not path.exists():
                logger.warning(f"Configuration file not found: {path}")
                return False
                
            if format == "yaml":
                content = read_text(path)
                if content is None:
                    return False
                config = yaml.safe_load(content)
            else:
                config = read_json(path)
                if config is None:
                    return False
                    
            # Update sections
            for section_name, section_data in config.items():
                section = self.get_section(section_name)
                for key, value in section_data.items():
                    section.set(key, value)
                    
            config_metrics['load'].labels(
                name=name,
                format=format
            ).inc()
            
            return True
            
        except Exception as e:
            error = handle_error(e, {
                "name": name,
                "format": format,
                "operation": "load_config"
            })
            logger.error(f"Error loading configuration: {str(error)}")
            config_metrics['error'].labels(
                name=name,
                operation="load",
                error_type=error.__class__.__name__
            ).inc()
            return False
            
    @log_operation('config_save', metrics=config_metrics['save'], duration=config_metrics['duration'])
    def save_config(self, name: str, format: Optional[str] = None) -> bool:
        """Save configuration to file.
        
        Args:
            name: Name of the configuration file (without extension)
            format: Optional file format override
            
        Returns:
            True if configuration saved successfully
        """
        try:
            format = format or self.default_format
            path = self.config_dir / f"{name}.{format}"
            
            # Convert sections to dictionary
            config = {}
            for section_name, section in self._sections.items():
                config[section_name] = {
                    key: config_value.value
                    for key, config_value in section._values.items()
                }
                
            # Save based on format
            if format == "yaml":
                content = yaml.dump(config)
                success = write_text(path, content) is not None
            else:
                success = write_json(path, config) is not None
                
            if success:
                config_metrics['save'].labels(
                    name=name,
                    format=format
                ).inc()
                
            return success
            
        except Exception as e:
            error = handle_error(e, {
                "name": name,
                "format": format,
                "operation": "save_config"
            })
            logger.error(f"Error saving configuration: {str(error)}")
            config_metrics['error'].labels(
                name=name,
                operation="save",
                error_type=error.__class__.__name__
            ).inc()
            return False
            
    def validate_all(self) -> bool:
        """Validate all configuration sections.
        
        Returns:
            True if all sections are valid
        """
        for section in self._sections.values():
            if not section.validate():
                return False
        return True 