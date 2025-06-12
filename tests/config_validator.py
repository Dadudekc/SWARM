"""
Tests for the configuration validator tool.
"""

import json
import os
from pathlib import Path
import unittest

import pytest

from agent_tools.general_tools.config_validator import ConfigValidator

class TestConfigValidator:
    """Test cases for the ConfigValidator class."""
    
    def test_valid_configs(self, test_config_dir):
        """Test validation of valid configuration files."""
        validator = ConfigValidator(config_dir=str(test_config_dir))
        results = validator.validate_all()
        
        assert len(results["valid"]) == 2
        assert len(results["invalid"]) == 0
        assert len(results["warnings"]) == 0
        assert len(results["unused"]) == 0
    
    def test_missing_required_field(self, test_config_dir):
        """Test detection of missing required field."""
        # Remove required field from response_loop_config.json
        config_path = test_config_dir / "response_loop_config.json"
        config = json.loads(config_path.read_text())
        del config["agent_id"]
        config_path.write_text(json.dumps(config))
        
        validator = ConfigValidator(config_dir=str(test_config_dir))
        results = validator.validate_all()
        
        assert len(results["valid"]) == 1
        assert len(results["invalid"]) == 1
        assert "response_loop_config.json" in [f["file"] for f in results["invalid"]]
    
    def test_invalid_type(self, test_config_dir):
        """Test detection of invalid field type."""
        # Change agent_id to integer in agent_config.json
        config_path = test_config_dir / "agent_config.json"
        config = json.loads(config_path.read_text())
        config["agent_id"] = 123
        config_path.write_text(json.dumps(config))
        
        validator = ConfigValidator(config_dir=str(test_config_dir))
        results = validator.validate_all()
        
        assert len(results["valid"]) == 1
        assert len(results["invalid"]) == 1
        assert "agent_config.json" in [f["file"] for f in results["invalid"]]
    
    def test_strict_mode(self, test_config_dir):
        """Test strict validation mode."""
        # Add unknown config file
        (test_config_dir / "unknown_config.json").write_text(
            json.dumps({"unknown": "value"})
        )
        
        validator = ConfigValidator(config_dir=str(test_config_dir), strict=True)
        results = validator.validate_all()
        
        assert len(results["valid"]) == 2
        assert len(results["invalid"]) == 1
        assert "unknown_config.json" in [f["file"] for f in results["invalid"]]
    
    def test_unused_config(self, test_config_dir):
        """Test detection of unused configuration file."""
        # Add unused config file
        (test_config_dir / "unused_config.json").write_text(
            json.dumps({"unused": "value"})
        )
        
        validator = ConfigValidator(config_dir=str(test_config_dir))
        results = validator.validate_all()
        
        assert len(results["valid"]) == 2
        assert len(results["unused"]) == 1
        assert "unused_config.json" in [f["file"] for f in results["unused"]]

if __name__ == '__main__':
    unittest.main() 