"""
Configuration Schema Validator
----------------------------
Validates YAML configuration files against a defined schema using Cerberus.
Includes advanced validation rules and runtime checks.
"""

from typing import Dict, Any, List, Optional, Tuple, Union
from cerberus import Validator
import logging
import os
import re
from pathlib import Path
from urllib.parse import urlparse
import yaml

from .utils import (
    VALID_LOG_LEVELS,
    VALID_MODES,
    validate_log_level,
    validate_mode,
    validate_path,
    validate_webhook_url,
    validate_ip,
    load_yaml,
    save_yaml
)

logger = logging.getLogger(__name__)

# Custom validation rules
def validate_url(field: str, value: str, error: Dict[str, Any]) -> None:
    """Validate URL format."""
    try:
        result = urlparse(value)
        if not all([result.scheme, result.netloc]):
            error[field] = "Invalid URL format"
    except Exception:
        error[field] = "Invalid URL format"

def validate_path_exists(field: str, value: str, error: Dict[str, Any]) -> None:
    """Validate that path exists."""
    if not os.path.exists(value):
        error[field] = f"Path does not exist: {value}"

def validate_command(field: str, value: str, error: Dict[str, Any]) -> None:
    """Validate command is allowed."""
    allowed_commands = ['git', 'python', 'pip', 'yaml', 'config']
    if value not in allowed_commands:
        error[field] = f"Command not allowed: {value}"

def validate_ip(field: str, value: str, error: Dict[str, Any]) -> None:
    """Validate IP address or CIDR format."""
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$'
    if not re.match(ip_pattern, value):
        error[field] = f"Invalid IP format: {value}"

# Schema definition for configuration validation
CONFIG_SCHEMA = {
    'agent': {
        'type': 'dict',
        'required': True,
        'schema': {
            'name': {
                'type': 'string',
                'required': True,
                'regex': '^[a-zA-Z0-9_-]+$'  # Alphanumeric with underscore and hyphen
            },
            'mode': {
                'type': 'string',
                'required': True,
                'allowed': list(VALID_MODES)
            },
            'log_level': {
                'type': 'string',
                'required': True,
                'allowed': list(VALID_LOG_LEVELS)
            },
            'webhook_url': {
                'type': 'string',
                'required': False,
                'nullable': True,
                'check_with': validate_url
            }
        }
    },
    'paths': {
        'type': 'dict',
        'required': True,
        'schema': {
            'inbox': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id}.*'  # Must contain {agent_id}
            },
            'outbox': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id}.*'
            },
            'processed': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id}.*'
            },
            'devlog': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id}.*'
            },
            'health': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id}.*'
            },
            'requests': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id}.*'
            }
        }
    },
    'tasks': {
        'type': 'dict',
        'required': True,
        'schema': {
            'max_retries': {
                'type': 'integer',
                'required': True,
                'min': 1,
                'max': 10
            },
            'backoff_factor': {
                'type': 'float',
                'required': True,
                'min': 1.0,
                'max': 5.0
            },
            'timeout': {
                'type': 'integer',
                'required': True,
                'min': 60,
                'max': 3600
            },
            'batch_size': {
                'type': 'integer',
                'required': True,
                'min': 1,
                'max': 100
            }
        }
    },
    'health': {
        'type': 'dict',
        'required': True,
        'schema': {
            'check_interval': {
                'type': 'integer',
                'required': True,
                'min': 10,
                'max': 300
            },
            'max_failures': {
                'type': 'integer',
                'required': True,
                'min': 1,
                'max': 10
            },
            'recovery_timeout': {
                'type': 'integer',
                'required': True,
                'min': 60,
                'max': 3600
            }
        }
    },
    'git': {
        'type': 'dict',
        'required': True,
        'schema': {
            'commit_message': {
                'type': 'string',
                'required': True,
                'regex': '.*{agent_id\}.*$'  # feat({agent_id}): message
            },
            'push_on_complete': {
                'type': 'boolean',
                'required': True
            },
            'branch': {
                'type': 'string',
                'required': True,
                'regex': '^[a-zA-Z0-9_-]+$'
            }
        }
    },
    'chatgpt': {
        'type': 'dict',
        'required': True,
        'schema': {
            'model': {
                'type': 'string',
                'required': True,
                'allowed': ['gpt-4', 'gpt-3.5-turbo']
            },
            'temperature': {
                'type': 'float',
                'required': True,
                'min': 0.0,
                'max': 1.0
            },
            'max_tokens': {
                'type': 'integer',
                'required': True,
                'min': 100,
                'max': 4000
            },
            'system_prompt': {
                'type': 'string',
                'required': True,
                'minlength': 10
            }
        }
    },
    'security': {
        'type': 'dict',
        'required': True,
        'schema': {
            'allowed_commands': {
                'type': 'list',
                'required': True,
                'schema': {
                    'type': 'string'
                }
            },
            'max_file_size': {
                'type': 'integer',
                'required': True,
                'min': 1024,
                'max': 10485760  # 10MB
            },
            'require_auth': {
                'type': 'boolean',
                'required': True
            },
            'allowed_ips': {
                'type': 'list',
                'required': True,
                'schema': {
                    'type': 'string'
                }
            }
        }
    }
}

class ConfigValidator:
    """Validates configuration against schema and performs additional checks."""
    
    def __init__(self):
        """Initialize the validator with schema."""
        self.validator = Validator(CONFIG_SCHEMA)
        self.validator.allow_unknown = False  # Strict validation
    
    def validate(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate configuration against schema.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, errors)
        """
        errors = []
        
        # Basic schema validation
        is_valid = self.validator.validate(config)
        if not is_valid:
            logger.error(f"Configuration validation failed: {self.validator.errors}")
            errors.extend(self.validator.errors.values())
            return False, errors
        
        # Additional validation checks
        additional_errors = {}
        
        # Validate paths
        path_errors = self._validate_paths(config, additional_errors)
        if path_errors:
            errors.extend(path_errors)
        
        # Validate webhook URL if present
        if 'agent' in config and 'webhook_url' in config['agent']:
            url_errors = self._validate_webhook_url(config['agent']['webhook_url'])
            if url_errors:
                errors.extend(url_errors)
        
        # Validate command paths
        cmd_errors = self._validate_command_paths(config)
        if cmd_errors:
            errors.extend(cmd_errors)
        
        # Validate IP addresses
        ip_errors = self._validate_ips(config)
        if ip_errors:
            errors.extend(ip_errors)
        
        if errors:
            return False, errors
        
        return True, []
    
    def _validate_paths(self, config: Dict[str, Any], errors: Dict[str, Any]) -> List[str]:
        """Validate path configurations.
        
        Args:
            config: Configuration dictionary
            errors: Dictionary to append errors to
            
        Returns:
            List of path validation errors
        """
        path_errors = []
        paths = config.get('paths', {})
        
        # Check for {agent_id} template in paths
        for key, path in paths.items():
            if '{agent_id}' not in path:
                path_errors.append(f"paths.{key}: Path must contain {{agent_id}} template")
            
            # Check for valid path characters
            if not re.match(r'^[a-zA-Z0-9/._-]+$', path):
                path_errors.append(f"paths.{key}: Path contains invalid characters: {path}")
        
        return path_errors
    
    def _validate_webhook_url(self, url: str) -> List[str]:
        """Validate webhook URL.
        
        Args:
            url: Webhook URL to validate
            
        Returns:
            List of URL validation errors
        """
        errors = []
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                errors.append("agent.webhook_url: Invalid URL format")
            if result.scheme not in ['http', 'https']:
                errors.append("agent.webhook_url: URL must use HTTP or HTTPS")
        except Exception:
            errors.append("agent.webhook_url: Invalid URL format")
        
        return errors
    
    def _validate_command_paths(self, config: Dict[str, Any]) -> List[str]:
        """Validate command paths exist in system.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of command validation errors
        """
        errors = []
        commands = config.get('security', {}).get('allowed_commands', [])
        
        for cmd in commands:
            # Check if command exists in PATH
            if not os.path.exists(f"/usr/bin/{cmd}") and not os.path.exists(f"/usr/local/bin/{cmd}"):
                errors.append(f"security.allowed_commands: Command {cmd} not found")
        
        return errors
    
    def _validate_ips(self, config: Dict[str, Any]) -> List[str]:
        """Validate IP addresses.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            List of IP validation errors
        """
        errors = []
        ips = config.get('security', {}).get('allowed_ips', [])
        
        for ip in ips:
            if not validate_ip(ip):
                errors.append(f"security.allowed_ips: Invalid IP address {ip}")
        
        return errors
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration that passes validation.
        
        Returns:
            Dictionary of default configuration
        """
        return {
            'agent': {
                'name': 'default',
                'mode': 'normal',
                'log_level': 'INFO',
                'webhook_url': None
            },
            'paths': {
                'inbox': '/data/{agent_id}/inbox',
                'outbox': '/data/{agent_id}/outbox',
                'processed': '/data/{agent_id}/processed',
                'devlog': '/data/{agent_id}/devlog',
                'health': '/data/{agent_id}/health',
                'requests': '/data/{agent_id}/requests'
            },
            'tasks': {
                'max_retries': 3,
                'backoff_factor': 2.0,
                'timeout': 300,
                'batch_size': 10
            },
            'health': {
                'check_interval': 60,
                'max_failures': 3,
                'recovery_timeout': 300
            },
            'git': {
                'commit_message': 'feat({agent_id}): {message}',
                'push_on_complete': True,
                'branch': 'main'
            },
            'chatgpt': {
                'model': 'gpt-4',
                'temperature': 0.7,
                'max_tokens': 2000,
                'system_prompt': 'You are a helpful AI assistant.'
            },
            'security': {
                'allowed_commands': ['git', 'python', 'pip'],
                'max_file_size': 10485760,  # 10MB
                'require_auth': True,
                'allowed_ips': ['127.0.0.1']
            }
        } 
