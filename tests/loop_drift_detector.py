"""
Tests for the loop drift detector tool.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from dreamos.core.monitor.loop_drift_detector import LoopDriftDetector

class TestLoopDriftDetector:
    """Test cases for the LoopDriftDetector class."""
    
    def test_no_drift(self, temp_dir):
        """Test when no drift is detected."""
        # Create test files
        agent_status = {
            "status": "active",
            "last_update": datetime.now().isoformat(),
            "agent_id": "test_agent"
        }
        (temp_dir / "agent_status.json").write_text(json.dumps(agent_status))
        
        detector = LoopDriftDetector(agent_dir=str(temp_dir))
        result = detector.check_drift()
        
        assert not result["drift_detected"]
        assert result["status"] == "active"
    
    def test_drift_detected(self, temp_dir):
        """Test when drift is detected."""
        # Create test files with old timestamp
        agent_status = {
            "status": "active",
            "last_update": (datetime.now() - timedelta(hours=2)).isoformat(),
            "agent_id": "test_agent"
        }
        (temp_dir / "agent_status.json").write_text(json.dumps(agent_status))
        
        detector = LoopDriftDetector(agent_dir=str(temp_dir))
        result = detector.check_drift()
        
        assert result["drift_detected"]
        assert result["status"] == "inactive"
    
    def test_missing_files(self, temp_dir):
        """Test handling of missing files."""
        detector = LoopDriftDetector(agent_dir=str(temp_dir))
        result = detector.check_drift()
        
        assert result["drift_detected"]
        assert result["status"] == "error"
        assert "missing" in result["message"].lower()
    
    def test_resume_agent(self, temp_dir):
        """Test resuming an agent."""
        # Create test files with old timestamp
        agent_status = {
            "status": "inactive",
            "last_update": (datetime.now() - timedelta(hours=2)).isoformat(),
            "agent_id": "test_agent"
        }
        (temp_dir / "agent_status.json").write_text(json.dumps(agent_status))
        
        detector = LoopDriftDetector(agent_dir=str(temp_dir))
        detector.resume_agent()
        
        # Check updated status
        updated_status = json.loads((temp_dir / "agent_status.json").read_text())
        assert updated_status["status"] == "active"
        assert "last_update" in updated_status 