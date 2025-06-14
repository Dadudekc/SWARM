"""
Config Validator
--------------
Validates configuration files for consistency and completeness.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validates configuration files."""
    
    def __init__(self, config_path: str = "config/"):
        """Initialize validator.
        
        Args:
            config_path: Path to config directory
        """
        self.config_path = Path(config_path)
        self.required_fields = {
            "response_loop_config.json": {
                "paths": ["bridge_outbox", "archive", "failed", "runtime"],
                "chatgpt": ["max_retries", "response_wait", "timeout"],
                "monitoring": ["enabled", "metrics_interval"]
            },
            "agent_config.json": {
                "agent_id": str,
                "capabilities": list,
                "memory": ["max_size", "cleanup_interval"]
            }
        }
    
    def validate_all(self, strict: bool = False) -> Dict[str, Any]:
        """Validate all config files.
        
        Args:
            strict: Whether to enforce strict validation
            
        Returns:
            Validation results dictionary
        """
        results = {
            "valid": [],
            "invalid": [],
            "warnings": [],
            "unused": []
        }
        
        # Find all config files
        config_files = list(self.config_path.glob("**/*.json"))
        
        # Track used configs
        used_configs = self._find_used_configs()
        
        for config_file in config_files:
            try:
                # Load config
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                # Validate structure
                validation = self._validate_config(config_file.name, config, strict)
                
                if validation["valid"]:
                    results["valid"].append(config_file.name)
                else:
                    results["invalid"].append({
                        "file": config_file.name,
                        "errors": validation["errors"]
                    })
                
                # Check for warnings
                if validation["warnings"]:
                    results["warnings"].append({
                        "file": config_file.name,
                        "warnings": validation["warnings"]
                    })
                
                # Check if config is used
                if config_file.name not in used_configs:
                    results["unused"].append(config_file.name)
                
            except Exception as e:
                logger.error(f"Error validating {config_file}: {e}")
                results["invalid"].append({
                    "file": config_file.name,
                    "errors": [str(e)]
                })
        
        return results
    
    def _validate_config(self, filename: str, config: Dict[str, Any], strict: bool) -> Dict[str, Any]:
        """Validate a single config file.
        
        Args:
            filename: Config file name
            config: Config dictionary
            strict: Whether to enforce strict validation
            
        Returns:
            Validation results dictionary
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Check if we have requirements for this file
        if filename not in self.required_fields:
            if strict:
                results["errors"].append(f"No validation rules for {filename}")
                results["valid"] = False
            else:
                results["warnings"].append(f"No validation rules for {filename}")
            return results
        
        # Validate required fields
        requirements = self.required_fields[filename]
        for section, fields in requirements.items():
            if section not in config:
                results["errors"].append(f"Missing section: {section}")
                results["valid"] = False
                continue
            
            if isinstance(fields, list):
                # Check required fields in section
                for field in fields:
                    if field not in config[section]:
                        results["errors"].append(f"Missing field: {section}.{field}")
                        results["valid"] = False
            elif isinstance(fields, type):
                # Check field type
                if not isinstance(config[section], fields):
                    results["errors"].append(
                        f"Invalid type for {section}: expected {fields.__name__}, got {type(config[section]).__name__}"
                    )
                    results["valid"] = False
        
        return results
    
    def _find_used_configs(self) -> Set[str]:
        """Find all config files referenced in code.
        
        Returns:
            Set of used config filenames
        """
        used_configs = set()
        
        # Search for config references
        for root, _, files in os.walk("."):
            for file in files:
                if file.endswith((".py", ".yaml", ".yml")):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            
                            # Look for config references
                            for config_file in self.required_fields.keys():
                                if config_file in content:
                                    used_configs.add(config_file)
                    except Exception as e:
                        logger.warning(f"Error reading {file_path}: {e}")
        
        return used_configs

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate configuration files")
    parser.add_argument("--path", default="config/", help="Path to config directory")
    parser.add_argument("--strict", action="store_true", help="Enforce strict validation")
    parser.add_argument("--output", help="Output file for results")
    args = parser.parse_args()
    
    try:
        # Initialize validator
        validator = ConfigValidator(args.path)
        
        # Validate configs
        results = validator.validate_all(args.strict)
        
        # Write results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
        else:
            print(json.dumps(results, indent=2))
        
        # Exit with status
        if results["invalid"]:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 